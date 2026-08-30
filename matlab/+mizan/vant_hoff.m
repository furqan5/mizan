function lk = vant_hoff(log_k25, delta_h_kcal, T_c)
%VANT_HOFF van't Hoff extrapolation of an equilibrium constant from 25 degC.
R = 8.314462;
T = T_c + 273.15;
lk = log_k25 - (delta_h_kcal*4184.0)/(2.302585*R)*(1.0/T - 1.0/298.15);
end
