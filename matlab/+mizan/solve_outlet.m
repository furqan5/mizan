function [T_wo, info] = solve_outlet(T_wi, T_db, rh, m_w, m_a, c, n, aw, p)
%SOLVE_OUTLET Cold-water outlet temperature [degC] by matching the Merkel
%   number the duty demands to the Merkel number the fill can supply.
%
%   The residual is monotone decreasing in T_wo but is not defined over the
%   whole interval -- a very low target drives the air deep into fog and the
%   integration fails -- so the bracket is found by a coarse scan from the
%   HOT end and the FIRST sign change is taken. Integration failure returns
%   a large positive sentinel, which puts a step discontinuity in the
%   residual; scanning from the hot end always returns the physical root
%   rather than the discontinuity.
if nargin < 8 || isempty(aw), aw = 1.0;     end
if nargin < 9 || isempty(p),  p = 101325.0; end
T_wo = NaN; info = [];

w_in = mizan.w_from_rh(T_db, rh, p);
T_wb = mizan.wetbulb(T_db, w_in, p);
Me_avail = mizan.merkel(m_w, m_a, c, n);

lo = T_wb + 0.05;  hi = T_wi - 0.02;
if hi <= lo, return, end

    function f = residual(t)
        rr = mizan.integrate_poppe(t, T_wi, T_db, w_in, m_w, m_a, aw, p);
        if isempty(rr), f = 1.0e3; else, f = rr.Me - Me_avail; end
    end

grid = linspace(hi, lo, 24);
prev_T = NaN; prev_f = NaN;
for i = 1:numel(grid)
    f = residual(grid(i));
    if ~isnan(prev_f) && prev_f*f <= 0
        T_wo = fzero(@residual, [grid(i) prev_T], optimset('TolX', 1e-8));
        info = mizan.integrate_poppe(T_wo, T_wi, T_db, w_in, m_w, m_a, aw, p);
        if isempty(info), T_wo = NaN; return, end
        info.T_wb     = T_wb;
        info.approach = T_wo - T_wb;
        info.range    = T_wi - T_wo;
        info.Q        = m_w*mizan.CPW()*(T_wi - T_wo);
        info.Me_fill  = Me_avail;
        return
    end
    prev_T = grid(i); prev_f = f;
end
end
