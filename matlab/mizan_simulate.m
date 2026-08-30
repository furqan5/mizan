%MIZAN_SIMULATE  Run the Simulink plant model and explain what happened.
%
%   Builds the model if it is not there, runs one Dhahran summer day, and
%   reports the result in plain English with one figure.
%
%   Run:  mizan_simulate
clear; clc; close all;
here = fileparts(mfilename('fullpath'));

if ~isfile(fullfile(here, 'mizan_plant.slx'))
    fprintf('building the model ...\n');
    build_mizan_model();
end

fprintf('%s\n', repmat('=', 1, 76));
fprintf('  MIZAN  --  Simulink plant model, one Dhahran summer day\n');
fprintf('  Furqan   The criterion for energy.\n');
fprintf('%s\n\n', repmat('=', 1, 76));

fprintf('what is in the model:\n');
fprintf('   the tower        validated Poppe heat-and-mass-transfer model\n');
fprintf('   the chiller      York YT 1758 kW, real manufacturer curves\n');
fprintf('   the loop         150 t of water as a Simscape thermal network,\n');
fprintf('                    which is what makes the plant slow to respond\n');
fprintf('   the chemistry    brucite saturation pH at the tube skin\n');
fprintf('   the supervisor   a Stateflow chart that starts read-only\n\n');

bdclose('all');
load_system('mizan_plant');
t0 = tic;
out = sim('mizan_plant');
fprintf('simulated 24 hours in %.0f seconds of wall clock.\n\n', toc(t0));

hr      = out.T_cold.Time/3600;
T_cold  = out.T_cold.Data;
T_hot   = out.T_hot.Data;
T_skin  = out.T_skin.Data;
pH_lim  = out.pH_limit.Data;
margin  = out.margin.Data;
P_ch    = out.P_chiller.Data;
P_fan   = out.P_fan.Data;
in_env  = out.in_env.Data;
mode    = out.mode.Data;

% drop the first sample: the Stateflow chart has not executed at t = 0, so
% its outputs are still at their initial zero and would misreport the state
k = 2:numel(hr);

fprintf('%s\n', repmat('-', 1, 76));
fprintf('  hour   cold water   hot water   tube skin   scale limit   state\n');
fprintf('%s\n', repmat('-', 1, 76));
for h = 0:2:22
    i = find(hr >= h, 1);
    if margin(i) < 0, st = 'DEPOSITING'; else, st = 'safe'; end
    fprintf('   %3d    %8.1f C  %8.1f C  %8.1f C   %8.2f     %s\n', ...
            h, T_cold(i), T_hot(i), T_skin(i), pH_lim(i), st);
end
fprintf('%s\n\n', repmat('-', 1, 76));

dep = margin(k) < 0;
fprintf('RESULT\n');
fprintf('   basin water          %.1f to %.1f C\n', min(T_cold(k)), max(T_cold(k)));
fprintf('   condenser tube skin  %.1f to %.1f C\n', min(T_skin(k)), max(T_skin(k)));
fprintf('   scale limit at skin  pH %.2f to %.2f  -- it MOVES, by %.2f pH units\n', ...
        min(pH_lim(k)), max(pH_lim(k)), max(pH_lim(k))-min(pH_lim(k)));
fprintf('   hours above the scaling limit: %.1f of 24\n', ...
        sum(dep)*(hr(2)-hr(1)));
fprintf('   chiller %.0f-%.0f kW, fan %.0f-%.0f kW\n', ...
        min(P_ch(k)), max(P_ch(k)), min(P_fan(k)), max(P_fan(k)));
fprintf('   entering condenser water stayed inside the chiller envelope: %s\n\n', ...
        ternary(all(in_env(k) > 0), 'yes, all day', 'NO -- see in_env'));

fprintf('WHAT A PLANT WOULD HAVE SEEN\n');
fprintf('   Conductivity and pH are held at setpoint, so both instruments\n');
fprintf('   read flat all day. The limit that actually matters moved by\n');
fprintf('   %.2f pH units, and nothing on the plant measures it.\n\n', ...
        max(pH_lim(k))-min(pH_lim(k)));

fprintf('SUPERVISOR\n');
names = {'FALLBACK','SHADOW','ADVISORY','CLOSED LOOP'};
fprintf('   spent the whole run in %s, which is correct: the product ships\n', ...
        names{round(median(mode(k)))+1});
fprintf('   read-only and does not earn write access for eight weeks.\n\n');

% ---------------------------------------------------------------------
f = figure('Color','w','Position',[60 50 1040 780], ...
           'Name','Mizan -- Simulink plant model');

subplot(3,1,1);
plot(hr, T_skin, 'LineWidth', 2.4, 'Color', [0.70 0.15 0.17]); hold on
plot(hr, T_hot,  'LineWidth', 1.8, 'Color', [0.08 0.26 0.36]);
plot(hr, T_cold, 'LineWidth', 1.8, 'Color', [0.11 0.45 0.58]);
ylabel('temperature  (\circC)'); xlim([0 24]); ylim([24 52]);
legend({'condenser tube skin -- where scale forms', ...
        'hot water leaving the condenser', ...
        'cold water leaving the tower'}, ...
       'Location','northwest','Box','off','FontSize',9);
title('The hottest surface in the plant is not measured anywhere', ...
      'FontWeight','bold');
grid on; box off;

subplot(3,1,2);
fill([hr; flipud(hr)], [pH_lim; repmat(8.7, numel(hr), 1)], ...
     [0.70 0.15 0.17], 'FaceAlpha', 0.16, 'EdgeColor','none'); hold on
p2 = plot(hr, pH_lim, 'LineWidth', 2.4, 'Color', [0.70 0.15 0.17]);
yline(8.7, '--', 'the loop actually runs here', 'LineWidth', 1.8, ...
      'Color', [0.08 0.26 0.36], 'LabelHorizontalAlignment','left');
ylabel('pH'); xlim([0 24]);
legend(p2, {'scale limit, at the tube skin'}, 'Location','southwest','Box','off');
title('The scale limit moves with load. The setpoint does not.', ...
      'FontWeight','bold');
grid on; box off;

subplot(3,1,3);
plot(hr, P_ch, 'LineWidth', 2.2, 'Color', [0.08 0.26 0.36]); hold on
plot(hr, P_fan, 'LineWidth', 2.2, 'Color', [0.11 0.45 0.58]);
ylabel('electrical power  (kW)'); xlabel('hour of the day'); xlim([0 24]);
legend({'chiller','cooling-tower fan'}, 'Location','northwest','Box','off');
title('Where the energy goes', 'FontWeight','bold');
grid on; box off;

outdir = fullfile(here, '..', 'figs');
if ~isfolder(outdir), mkdir(outdir); end
exportgraphics(f, fullfile(outdir, 'matlab_simulink_day.png'), 'Resolution', 160);
fprintf('figure written -> figs/matlab_simulink_day.png\n');

S = struct('T_cold_min', min(T_cold(k)), 'T_cold_max', max(T_cold(k)), ...
           'T_skin_min', min(T_skin(k)), 'T_skin_max', max(T_skin(k)), ...
           'pH_limit_min', min(pH_lim(k)), 'pH_limit_max', max(pH_lim(k)), ...
           'hours_depositing', sum(dep)*(hr(2)-hr(1)), ...
           'P_chiller_min', min(P_ch(k)), 'P_chiller_max', max(P_ch(k)), ...
           'in_envelope_all_day', all(in_env(k) > 0));
fid = fopen(fullfile(here, '..', 'results', 'matlab_simulink.json'), 'w');
fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
fprintf('results written -> results/matlab_simulink.json\n');

function s = ternary(c, a, b)
    if c, s = a; else, s = b; end
end
