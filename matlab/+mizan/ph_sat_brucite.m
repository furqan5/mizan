function pH_s = ph_sat_brucite(T_c, w)
%PH_SAT_BRUCITE Saturation pH for Mg(OH)2 (brucite) at temperature T_c.
%
%   THIS IS GATE V6, AND IT IS THE SHARPEST RESULT IN THE PACKAGE.
%
%   Magnesium silicate scale forms in two steps: brucite precipitates
%   first, then reacts with dissolved and colloidal silica in the boundary
%   layer to form the dense silicate scale. Brucite's saturation pH is
%   RETROGRADE -- it FALLS as temperature rises -- so deposition cannot
%   occur while bulk pH stays below the saturation pH evaluated at the
%   HOTTEST surface in the system, which is the condenser tube skin.
%
%   The consequence a plant can see: the same tower deposits at high load
%   and not at low load, with pH and conductivity reading identical in both
%   cases. No fixed pH setpoint can express that, because the limit moves
%   with the skin temperature and the skin temperature moves with load.
%
%   Mg(OH)2 = Mg+2 + 2 OH-, phreeqc.dat log_k -11.18, delta_h -27.1 kcal.
log_k = mizan.vant_hoff(-11.18, -27.1, T_c);
m_Mg = w.Mg*1e-3/24.305;
if m_Mg <= 0, pH_s = Inf; return, end
I = mizan.ionic_strength(w);
a_mg = m_Mg*mizan.davies_gamma(2, I, T_c);
log_a_oh = (log_k - log10(a_mg))/2.0;
pOH = -log_a_oh;
kw = mizan.vant_hoff(-14.0, 13.362, T_c);
pH_s = -kw - pOH;
end
