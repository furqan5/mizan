function r = integrate_poppe(T_wo, T_wi, T_db, w_in, m_w_in, m_a, aw, p, n_steps)
%INTEGRATE_POPPE Integrate the Poppe equations from the cold end upward.
%   Counterflow: air enters at the bottom, where the water leaves, so the
%   air inlet state is the initial condition at T_w = T_wo.
%
%   Fixed-step classical RK4, not an adaptive solver, for the same three
%   reasons as the Python core: bounded deterministic runtime (a supervisory
%   controller has a control interval to meet), a smooth integrand away from
%   the branch switch, and identical arithmetic on desktop and edge target.
%
%   Returns [] where the integration leaves physics, which is how the caller
%   detects a duty the tower cannot deliver.
if nargin < 7 || isempty(aw),      aw = 1.0;        end
if nargin < 8 || isempty(p),       p = 101325.0;    end
if nargin < 9 || isempty(n_steps), n_steps = 160;   end
r = [];
if ~(T_wi > T_wo), return, end

h = (T_wi - T_wo)/n_steps;
y = [w_in; T_db; 0.0; m_w_in];
T = T_wo;
for k = 1:n_steps
    k1 = mizan.poppe_derivs(T,         y,            m_a, aw, p);
    k2 = mizan.poppe_derivs(T + 0.5*h, y + 0.5*h*k1, m_a, aw, p);
    k3 = mizan.poppe_derivs(T + 0.5*h, y + 0.5*h*k2, m_a, aw, p);
    k4 = mizan.poppe_derivs(T + h,     y + h*k3,     m_a, aw, p);
    y = y + h/6.0*(k1 + 2*k2 + 2*k3 + k4);
    T = T + h;
    if any(~isfinite(y)), return, end
    if y(1) < 0.0 || y(1) > 1.0, return, end   % humidity ratio left physics
end

w_out = y(1); T_a_out = y(2); Me = y(3); m_w_top = y(4);
if Me <= 0.0 || ~isfinite(Me), return, end

r = struct( ...
    'Me',      Me, ...
    'w_out',   w_out, ...
    'T_a_out', T_a_out, ...
    'm_evap',  m_a*(w_out - w_in), ...
    'm_w_top', m_w_top, ...
    'fogged',  w_out > mizan.ws(T_a_out, p, 1.0));
end
