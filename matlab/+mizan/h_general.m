function h = h_general(T_a, w, p)
%H_GENERAL Air-stream enthalpy [kJ/kg dry air], valid on both sides of
%   saturation. Above saturation the air is saturated and the excess
%   humidity ratio is carried as suspended liquid (fog), which is how
%   Poppe treats supersaturated tower air.
w_sa = mizan.ws(T_a, p, 1.0);
if w > w_sa
    h = mizan.hmoist(T_a, w_sa) + (w - w_sa)*mizan.CPW()*T_a;
else
    h = mizan.hmoist(T_a, w);
end
end
