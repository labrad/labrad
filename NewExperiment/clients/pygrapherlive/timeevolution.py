import numpy as np
from scipy.special.orthogonal import eval_genlaguerre as laguer

class time_evolution():#contains all relevant functions for thermal states, rabi flops and dephasing
    def __init__(self, trap_frequency, projection, sideband_order,nmax = 1000):
        from labrad import units as U
        m = 40 * U.amu
        hbar = U.hbar
        wavelength= U.WithUnit(729,'nm')
        
        self.sideband_order = sideband_order
        self.n = np.linspace(0, nmax,nmax +1)
        self.eta = 2.*np.cos(projection)*np.pi/wavelength['m']*np.sqrt(hbar['J*s']/(2.*m['kg']*2.*np.pi*trap_frequency['Hz']))
        self.rabi_coupling=self.rabi_coupling()
        
    def rabi_coupling(self):
        eta = self.eta
        n = self.n
        sideband=np.abs(self.sideband_order)
        x=1
        for k in np.linspace(1,sideband,sideband):
            x=x*(n+k)
        result = (eta**sideband)*np.exp(-.5*eta**2.)*laguer(n,sideband,eta**2.)/np.sqrt(x)
        return result
        
    def p_thermal(self,nbar):
        n = self.n
        sideband = self.sideband_order
        nplus=0
        if sideband<0:
            nplus=-sideband
        #level population probability for a given nbar, see Leibfried 2003 (57)
        nbar=np.float64(nbar)
        p = ((nbar/(nbar+1.))**(n+nplus))/(nbar+1.)
        pp=np.sum(((nbar/(nbar+1.))**(np.linspace(-nplus,-1,nplus)+nplus))/(nbar+1.),axis=0)
        one=np.sum(p,axis=0)+pp
        if np.abs(1-one)>0.00001:
            print 'Warning: nmax may not be high enough for chosen value of nbar = {0}\nmissing probability = {1}'.format(nbar,1-one)
        return p
    
    def state_evolution(self, t, nbar, f_Rabi, delta=0.0):
        ones = np.ones_like(t)
        p = self.p_thermal(nbar)
        g_to_e = self.g_to_e_prob(t, f_Rabi, delta)
        result = np.sum(np.outer(p, ones) * g_to_e, axis = 0)
        return result
    
    def state_evolution_fluc(self,t,nbar,f_Rabi,delta_center,delta_variance,n_fluc=5.0):
        evo_list=[]
        i_list=np.linspace(-1,1,n_fluc)*np.exp(-np.linspace(-1,1,n_fluc)**2/2.0)/np.sqrt(2.0*np.pi)
        for i in i_list:
            evo_list.append(self.state_evolution(t,nbar,f_Rabi,delta_center+delta_variance*i))
        result = np.sum(evo_list,axis=0)/float(n_fluc)
        return result

    def deph_evolution_fluc(self,t,t0,nbar,f_Rabi,delta_center,delta_variance,n_fluc=5.0):
        evo_list=[]
        i_list=np.linspace(-1,1,n_fluc)*np.exp(-np.linspace(-1,1,n_fluc)**2/2.0)/np.sqrt(2.0*np.pi)
        for i in i_list:
            evo_list.append(self.deph_evolution(t,t0,nbar,f_Rabi,delta_center+delta_variance*i))
        result = np.sum(evo_list,axis=0)/float(n_fluc)
        return result
    
    def g_to_e_prob(self,t,f_Rabi,delta):#absolute value of u^{eg}_{nm}(t), is equal to e_to_g_prob
        omega_eff = self.rabi_coupling*2.0*np.pi*f_Rabi
        delta = 2.0*np.pi*delta
        omega = np.sqrt(omega_eff**2+delta**2)
        ones = np.ones_like(t)
        result = np.outer(omega_eff**2/omega**2,ones)*np.sin(np.outer(omega/2.0,t))**2
        return result

    def g_to_g_prob(self,t,f_Rabi,delta):#absolute value of u^{gg}_{nm}(t), is equal to e_to_e_prob
        omega_eff = self.rabi_coupling*2.0*np.pi*f_Rabi
        delta = 2.0*np.pi*delta
        omega = np.sqrt(omega_eff**2+delta**2)
        ones = np.ones_like(t)
        result = np.cos(np.outer(omega/2.0,t))**2+np.outer(delta/omega,ones)**2*np.sin(np.outer(omega/2.0,t))**2
        return result
    
    def deph_evolution(self,t,t0,nbar,f_Rabi,delta=0.0):
        p=self.p_thermal(nbar)
        def pge(t):
            return self.g_to_e_prob(t, f_Rabi, delta)
        def pgg(t):
            return self.g_to_g_prob(t, f_Rabi, delta)
        ones = np.ones_like(t)
        t0=ones*t0
        result=np.sum(np.outer(p,ones)*(pgg(t0)*pge(t-t0)+pge(t0)*pgg(t-t0)),axis=0)
        return result