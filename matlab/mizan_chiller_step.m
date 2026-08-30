function [P_chiller, in_env] = mizan_chiller_step(Q_evap, T_cold)
%MIZAN_CHILLER_STEP  One chiller evaluation, for the Simulink model.
%   IN_ENV is 0 when entering condenser water leaves the range the
%   manufacturer's curves were fitted in -- which is also the machine's
%   permitted operating window.
[P_chiller, ~, ok] = mizan.chiller_power(Q_evap, T_cold, 7.0, 10000);
in_env = double(ok);
end
