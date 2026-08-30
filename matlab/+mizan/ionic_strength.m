function I = ionic_strength(w)
%IONIC_STRENGTH Ionic strength [mol/kg] of a water analysis in mg/L.
sp = {'Ca',40.078,2; 'Mg',24.305,2; 'Na',22.990,1; 'K',39.098,1; ...
      'HCO3',61.017,-1; 'SO4',96.06,-2; 'Cl',35.453,-1; 'NO3',62.004,-1};
I = 0;
for i = 1:size(sp,1)
    m = w.(sp{i,1})*1e-3/sp{i,2};
    I = I + 0.5*m*sp{i,3}^2;
end
end
