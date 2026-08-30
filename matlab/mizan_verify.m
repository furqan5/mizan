%MIZAN_VERIFY  Does the MATLAB twin agree with the validated Python core?
%
%   A second implementation of the same physics is worth nothing unless it
%   is shown to agree with the one that was actually validated against
%   experiment. This script scores that agreement against thresholds fixed
%   BEFORE it was first run, in the same way as every other gate in this
%   package.
%
%   It reads a case file written by the Python side
%   (python src/export_matlab_cases.py) so that both implementations are
%   answering identical questions.
%
%   Run:  mizan_verify
clear; clc;
here = fileparts(mfilename('fullpath'));
addpath(here);
casefile = fullfile(here, '..', 'results', 'matlab_cases.json');

% ---- gates, fixed before the first run --------------------------------
GATE.Tout_max_abs_K   = 0.010;   % 1/50 of the core's own holdout error
GATE.evap_max_pct     = 0.50;
GATE.chiller_max_pct  = 0.10;
GATE.pHs_max_abs      = 0.005;

fprintf('%s\n', repmat('=', 1, 74));
fprintf('MIZAN :: MATLAB twin vs the validated Python core\n');
fprintf('%s\n', repmat('=', 1, 74));
fprintf('agreement gates, fixed before this was first run:\n');
fprintf('   outlet water temperature   |dT|   <= %.3f K\n', GATE.Tout_max_abs_K);
fprintf('   evaporation rate           |d|    <= %.2f %%\n', GATE.evap_max_pct);
fprintf('   chiller electrical power   |d|    <= %.2f %%\n', GATE.chiller_max_pct);
fprintf('   brucite saturation pH      |d|    <= %.3f\n\n', GATE.pHs_max_abs);

if ~isfile(casefile)
    error(['Case file not found: %s\n' ...
           'Generate it first with:  python src/export_matlab_cases.py'], casefile);
end
C = jsondecode(fileread(casefile));
fprintf('%d cases, fill law Me = %.4f (m_w/m_a)^(%.4f)\n\n', ...
        numel(C.cases), C.fill_c, C.fill_n);

n = numel(C.cases);
dT = nan(n,1); de = nan(n,1);
for i = 1:n
    c = C.cases(i);
    [t, info] = mizan.solve_outlet(c.T_wi, c.T_db, c.rh, c.m_w, c.m_a, ...
                                   C.fill_c, C.fill_n, c.aw);
    if isempty(info), continue, end
    dT(i) = t - c.T_wo;
    de(i) = 100*(info.m_evap - c.m_evap)/c.m_evap;
end
ok = ~isnan(dT);

nc = numel(C.chiller);
dp = nan(nc,1);
for i = 1:nc
    c = C.chiller(i);
    P = mizan.chiller_power(c.Q_evap_kW, c.T_cws, c.T_chws, c.Q_ref_kW);
    dp(i) = 100*(P - c.P_kW)/c.P_kW;
end

nb = numel(C.brucite);
db = nan(nb,1);
for i = 1:nb
    c = C.brucite(i);
    w = mizan.water_aramco(c.cycles, c.SiO2);
    db(i) = mizan.ph_sat_brucite(c.T_c, w) - c.pH_s;
end

% ---- score ------------------------------------------------------------
rows = { ...
 'outlet water temperature', max(abs(dT(ok))), 'K',  GATE.Tout_max_abs_K,  sum(ok); ...
 'evaporation rate',         max(abs(de(ok))), '%',  GATE.evap_max_pct,    sum(ok); ...
 'chiller electrical power', max(abs(dp)),     '%',  GATE.chiller_max_pct, nc; ...
 'brucite saturation pH',    max(abs(db)),     '',   GATE.pHs_max_abs,     nb};

fprintf('%s\n', repmat('-', 1, 74));
fprintf('%-28s %10s %-3s %10s  %5s  %s\n', 'quantity', 'worst case', '', 'limit', 'n', '');
fprintf('%s\n', repmat('-', 1, 74));
allpass = true;
for i = 1:size(rows,1)
    pass = rows{i,2} <= rows{i,4};
    allpass = allpass && pass;
    if pass, v = 'PASS'; else, v = 'FAIL'; end
    fprintf('%-28s %10.6f %-3s %10.4f  %5d  %s\n', ...
            rows{i,1}, rows{i,2}, rows{i,3}, rows{i,4}, rows{i,5}, v);
end
fprintf('%s\n', repmat('-', 1, 74));
if allpass
    fprintf('\nThe MATLAB twin reproduces the validated core. Any result the\n');
    fprintf('Simulink model produces can be traced back to the same physics\n');
    fprintf('that was scored against the Almeria experiment.\n');
else
    fprintf('\nThe twin does NOT reproduce the core. Do not use it until it does.\n');
end
