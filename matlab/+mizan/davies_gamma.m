function g = davies_gamma(z, I, T_c)
%DAVIES_GAMMA Davies activity coefficient. Valid to I ~ 0.5 mol/kg.
if nargin < 3 || isempty(T_c), T_c = 25.0; end
T = T_c + 273.15;
eps = 87.74 - 0.4008*T_c + 9.398e-4*T_c^2 - 1.410e-6*T_c^3;
A = 1.82483e6/(eps*T)^1.5;
s = sqrt(I);
g = 10.0^(-A*z^2*(s/(1.0 + s) - 0.3*I));
end
