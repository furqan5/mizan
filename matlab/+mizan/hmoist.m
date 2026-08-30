function h = hmoist(T, W)
%HMOIST Moist-air specific enthalpy [kJ/kg dry air]. ASHRAE Eq. (30).
h = 1.006*T + W.*(2501.0 + 1.860*T);
end
