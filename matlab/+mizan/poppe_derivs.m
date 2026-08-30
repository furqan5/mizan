function dy = poppe_derivs(T_w, y, m_a, aw, p)
%POPPE_DERIVS Poppe ODE right-hand side, d/dT_w of [w, T_a, Me, m_w].
%   Two branches per Kloppers & Kroeger (2005): the unsaturated set and the
%   supersaturated set used once the air stream has fogged. The state
%   carries air DRY-BULB rather than enthalpy so the saturation test is
%   direct and the branch switch is continuous in the state.
w = y(1); T_a = y(2); m_w = y(4);

% interface saturation is evaluated at the water activity of the
% circulating water -- the salinity coupling
w_sw  = mizan.ws(T_w, p, aw);
h_asw = mizan.hmoist(T_w, w_sw);
w_sa  = mizan.ws(T_a, p, 1.0);
h_v   = 2501.6 + 1.868*T_w;              % saturated vapour enthalpy

supersaturated = w > w_sa;
if supersaturated
    h_air = mizan.hmoist(T_a, w_sa) + (w - w_sa)*mizan.CPW()*T_a;
    drive = w_sw - w_sa;
    Lef   = mizan.lewis_factor(w_sa, w_sw);
else
    h_air = mizan.hmoist(T_a, w);
    drive = w_sw - w;
    Lef   = mizan.lewis_factor(w, w_sw);
end

denom = (h_asw - h_air) + (Lef - 1.0)*((h_asw - h_air) - drive*h_v) ...
        - drive*mizan.CPW()*T_w;
if abs(denom) < 1e-8
    if denom >= 0, denom = 1e-8; else, denom = -1e-8; end
end

ratio = m_w / m_a;
dw  = mizan.CPW()*ratio*drive/denom;
dh  = mizan.CPW()*ratio + mizan.CPW()*T_w*dw;   % energy balance incl. evaporation
dMe = mizan.CPW()/denom;

if supersaturated                                % differentiate fogged enthalpy
    e = 1e-5;
    dh_dTa = (mizan.h_general(T_a+e, w, p) - mizan.h_general(T_a-e, w, p))/(2*e);
    dh_dw  = (mizan.h_general(T_a, w+e, p) - mizan.h_general(T_a, w-e, p))/(2*e);
else
    dh_dTa = 1.006 + 1.86*w;
    dh_dw  = 2501.0 + 1.86*T_a;
end

dT_a = (dh - dh_dw*dw)/dh_dTa;
dmw  = m_a*dw;
dy = [dw; dT_a; dMe; dmw];
end
