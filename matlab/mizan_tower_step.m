function [T_cold, m_evap, UA, T_wb] = mizan_tower_step(T_hot, T_db, rh, fan_pct)
%MIZAN_TOWER_STEP  One tower evaluation, for the Simulink model.
%
%   Wraps the validated Poppe model. Also returns UA, an equivalent
%   heat-transfer conductance [kW/K] between the loop water and the ambient
%   wet-bulb, which is what the Simscape thermal network needs in order to
%   carry the loop's thermal inertia:
%
%       Q = UA * (T_loop - T_wetbulb)
%
%   so  UA = Q / (T_hot - T_wetbulb)  at the operating point the Poppe
%   model just solved. This is not an extra assumption -- it is the same
%   heat duty, re-expressed in the form a physical network can use.
persistent P
if isempty(P)
    P = load_plant();
end

m_a = P.m_a_rated * max(min(fan_pct, 100), 0) / 100;
[T_cold, info] = mizan.solve_outlet(T_hot, T_db, rh, P.m_w, m_a, ...
                                    P.fill_c, P.fill_n);
if isempty(info) || ~isfinite(T_cold)
    % The tower cannot meet this duty. Report the incumbent setpoint and a
    % small conductance rather than a NaN, and let the supervisor's fault
    % path deal with it -- a controller must degrade, not crash.
    T_cold = T_hot;  m_evap = 0;  UA = 1e-3;
    T_wb = mizan.wetbulb_from_rh(T_db, rh);
    return
end

m_evap = info.m_evap;
T_wb = info.T_wb;
dT = max(T_hot - info.T_wb, 0.1);
UA = (P.m_w * mizan.CPW() * (T_hot - T_cold)) / dT;    % kW/K
end


function P = load_plant()
here = fileparts(mfilename('fullpath'));
cal = jsondecode(fileread(fullfile(here, '..', 'results', 'calibration.json')));
P.fill_c = cal.fill_c;
P.fill_n = cal.fill_n;
P.m_w = 478;  P.m_a_rated = 400;  P.p_fan_rated = 110;
P.Q_evap_kW = 10000;
end
