%MIZAN_DEMO  One day in a Gulf district-cooling plant, explained.
%
%   You do not need to know any thermodynamics to read the output of this
%   script. It prints, in plain English, what happens to a cooling tower
%   over a single hot day, and it shows the one thing the plant's own
%   instruments cannot see.
%
%   THE SHORT VERSION
%
%   A district-cooling plant rejects heat by evaporating water in a cooling
%   tower. As water evaporates it leaves its dissolved minerals behind, so
%   the water going round the loop gets saltier and saltier. Let it get too
%   salty and minerals crystallise on the inside of the condenser tubes --
%   scale -- and the plant loses efficiency and eventually has to be shut
%   down and cleaned.
%
%   To stop that, operators throw some of the water away (blowdown) and
%   replace it with fresh water (makeup). Throw away too little and you get
%   scale. Throw away too much and you waste water, which in the Gulf is
%   desalinated and expensive.
%
%   Everyone knows this. What nobody currently measures is WHERE the scale
%   actually forms. It does not form in the bulk of the water, which is
%   what the plant's sensors measure. It forms on the hottest surface in
%   the system: the skin of the condenser tube, several degrees hotter than
%   the water around it. And for one important scale-forming mineral, the
%   limit gets TIGHTER as that surface gets hotter -- so the same tower,
%   with identical sensor readings, is safe at low load and depositing
%   scale at high load.
%
%   That is what this script shows.
%
%   Run:  mizan_demo
clear; clc; close all;

fprintf('%s\n', repmat('=', 1, 76));
fprintf('  MIZAN  --  one day in a Gulf district-cooling plant\n');
fprintf('  Furqan   The criterion for energy.\n');
fprintf('%s\n\n', repmat('=', 1, 76));

% ---------------------------------------------------------------------
% THE PLANT.  A 10 MW condenser-water module -- one cell of a larger
% district-cooling plant, about 2,800 tons of refrigeration.
% ---------------------------------------------------------------------
plant.Q_evap_kW    = 10000;   % cooling delivered to the district
plant.m_w          = 478;     % condenser water going round the loop [kg/s]
plant.m_a_rated    = 400;     % air the fans can move at full speed  [kg/s]
plant.p_fan_rated  = 110;     % fan power at full speed             [kW]
plant.skin_delta_K = 8.0;     % how much hotter the tube skin is than the
                              % water around it, when the tube is fouled

here = fileparts(mfilename('fullpath'));
cal = jsondecode(fileread(fullfile(here, '..', 'results', 'calibration.json')));
fill_c = cal.fill_c;  fill_n = cal.fill_n;

% ---------------------------------------------------------------------
% THE DAY.  A Dhahran summer day: cool at dawn, brutal in the afternoon.
% Cooling demand follows the heat, as it does in every real plant.
% ---------------------------------------------------------------------
hour  = 0:23;
s     = sin(pi*max(hour-6,0)/16).^2;
T_db  = 32 + 12*s;        % 32 C at night, 44 C at peak
rh    = 0.55 - 0.25*s;    % drier as it heats
load  = 0.62 + 0.38*s;    % 62 % at night, 100 % at peak

fprintf('The day:   %.0f-%.0f C dry bulb, cooling load %.0f-%.0f %% of design.\n', ...
        min(T_db), max(T_db), 100*min(load), 100*max(load));
fprintf('The water: measured Saudi Aramco reclaimed water, run at 4 cycles\n');
fprintf('           of concentration -- the industry norm.\n');
fprintf('The tower: fan held at a fixed 85 %%, which is how a building\n');
fprintf('           management system runs one today.\n\n');

cycles   = 4.0;
bulk_pH  = 8.7;        % where a Gulf reclaimed-water loop actually sits
fan_pct  = 85.0;

n = numel(hour);
T_cold = nan(1,n); T_hot = nan(1,n); T_skin = nan(1,n);
pH_limit = nan(1,n); P_chill = nan(1,n); P_fan = nan(1,n); cond_uS = nan(1,n);

w_loop = mizan.water_aramco(cycles, 26.8);

for i = 1:n
    Q = plant.Q_evap_kW*load(i);
    m_a = plant.m_a_rated*fan_pct/100;

    % Solve tower and chiller together: the tower has to reject the
    % cooling load PLUS the compressor work, and the compressor work
    % depends on how cold the tower manages to get the water. Neither can
    % be worked out without the other, so it is iterated to agreement.
    T_wo = 33; info = [];
    for it = 1:80
        P = mizan.chiller_power(Q, T_wo, 7.0, plant.Q_evap_kW);
        Q_cond = Q + P;
        T_wi = T_wo + Q_cond/(plant.m_w*mizan.CPW());
        [T_new, info] = mizan.solve_outlet(T_wi, T_db(i), rh(i), ...
                                           plant.m_w, m_a, fill_c, fill_n);
        if isempty(info), break, end
        if abs(T_new - T_wo) < 1e-6, T_wo = T_new; break, end
        T_wo = T_new;
    end
    if isempty(info), continue, end

    T_cold(i)  = T_wo;
    T_hot(i)   = T_wi;
    T_skin(i)  = T_wi + plant.skin_delta_K;
    P_chill(i) = P;
    P_fan(i)   = plant.p_fan_rated*(m_a/plant.m_a_rated)^3;

    % THE LIMIT NOBODY MEASURES: the pH above which magnesium silicate
    % starts to deposit, evaluated at the tube skin. It FALLS as the skin
    % gets hotter, which is the opposite of what intuition suggests.
    pH_limit(i) = mizan.ph_sat_brucite(T_skin(i), w_loop);

    % what the plant's own instruments read -- both essentially constant
    cond_uS(i) = 1.55*w_loop.TDS;         % conductivity, uS/cm
end

% ---------------------------------------------------------------------
% WHAT HAPPENED
% ---------------------------------------------------------------------
margin = pH_limit - bulk_pH;          % positive = safe, negative = depositing
depositing = margin < 0;

fprintf('%s\n', repmat('-', 1, 76));
fprintf('  hour  air C  load %%   cold water C  tube skin C  scale limit pH  state\n');
fprintf('%s\n', repmat('-', 1, 76));
for i = 1:2:n
    if depositing(i), st = 'DEPOSITING'; else, st = 'safe'; end
    fprintf('    %2d  %5.1f  %5.0f      %8.1f    %9.1f      %8.2f   %s\n', ...
            hour(i), T_db(i), 100*load(i), T_cold(i), T_skin(i), pH_limit(i), st);
end
fprintf('%s\n\n', repmat('-', 1, 76));

fprintf('WHAT THE PLANT''S OWN SENSORS SAW ALL DAY\n');
fprintf('   conductivity  %.0f uS/cm  ->  %.0f uS/cm   (change: %.1f %%)\n', ...
        cond_uS(1), cond_uS(end), 100*(cond_uS(end)/cond_uS(1)-1));
fprintf('   pH            %.2f         ->  %.2f          (change: none)\n\n', ...
        bulk_pH, bulk_pH);

fprintf('WHAT WAS ACTUALLY HAPPENING\n');
[mx, imx] = max(pH_limit); [mn, imn] = min(pH_limit);
fprintf('   The scale limit fell from pH %.2f at %02d:00 to pH %.2f at %02d:00,\n', ...
        mx, hour(imx), mn, hour(imn));
fprintf('   because the tube skin went from %.0f C to %.0f C as the load rose.\n', ...
        min(T_skin), max(T_skin));
if any(depositing)
    d = find(depositing);
    fprintf('   For %d hours of the day -- %02d:00 to %02d:00 -- the loop sat above\n', ...
            numel(d), hour(d(1)), hour(d(end)));
    fprintf('   its own scaling limit and was depositing magnesium silicate.\n\n');
    fprintf('   Both instruments read flat through all of it.\n\n');
else
    fprintf('   The loop stayed below its scaling limit all day. The worst-case\n');
    fprintf('   margin was %.2f pH units at %02d:00 -- and a margin that small,\n', ...
            min(margin), hour(margin==min(margin)));
    fprintf('   invisible to every instrument on the plant, is the whole point.\n\n');
end

fprintf('WHY THIS NEEDS THREE MODELS AT ONCE\n');
fprintf('   The skin temperature comes from the THERMAL model.\n');
fprintf('   The pH limit at that temperature comes from the CHEMISTRY model.\n');
fprintf('   Moving the loop back under the limit needs the ACID actuator.\n');
fprintf('   A water-treatment controller has the chemistry and the actuator\n');
fprintf('   but no skin temperature. A building management system has the\n');
fprintf('   thermal model but no chemistry. Neither one can see this.\n\n');

% ---------------------------------------------------------------------
% ONE FIGURE, IN PLAIN LANGUAGE
% ---------------------------------------------------------------------
f = figure('Color','w','Position',[80 60 1020 760],'Name','Mizan -- one Gulf day');

subplot(3,1,1);
plot(hour, T_skin, 'LineWidth', 2.4, 'Color', [0.70 0.15 0.17]); hold on
plot(hour, T_hot,  'LineWidth', 1.8, 'Color', [0.08 0.26 0.36]);
plot(hour, T_cold, 'LineWidth', 1.8, 'Color', [0.11 0.45 0.58]);
ylabel('temperature  (\circC)');
legend({'condenser tube skin -- where scale forms', ...
        'hot water leaving the condenser', ...
        'cold water leaving the tower'}, 'Location','northwest','Box','off', ...
       'FontSize', 9);
ylim([25 52]);
title('The hottest surface in the plant is not measured anywhere', ...
      'FontWeight','bold');
grid on; box off; xlim([0 23]);

subplot(3,1,2);
fill([hour fliplr(hour)], [pH_limit repmat(bulk_pH,1,n)], [0.70 0.15 0.17], ...
     'FaceAlpha', 0.16, 'EdgeColor','none'); hold on
p2 = plot(hour, pH_limit, 'LineWidth', 2.4, 'Color', [0.70 0.15 0.17]);
yline(bulk_pH, '--', 'the loop actually runs here', 'LineWidth', 1.8, ...
      'Color', [0.08 0.26 0.36], 'LabelHorizontalAlignment','left');
ylabel('pH');
legend(p2, {'scale limit, evaluated at the tube skin'}, ...
       'Location','southwest','Box','off');
title('The scale limit moves with load. The setpoint does not.', ...
      'FontWeight','bold');
grid on; box off; xlim([0 23]);

subplot(3,1,3);
% Both traces are deliberately flat -- that IS the result. But if both axes
% are centred on their own constant, the two lines land on the same pixel
% row and the second drawn hides the first, which reads as a broken plot
% rather than as the point. The limits below are therefore ASYMMETRIC, so
% conductivity sits low in the frame and pH sits high, and both are visible.
yyaxis left
plot(hour, cond_uS, 'LineWidth', 2.4); ylabel('conductivity  (\muS/cm)');
c0 = mean(cond_uS);
ylim([c0*0.94 c0*1.24]);                 % trace sits ~20 % up the frame
yyaxis right
plot(hour, repmat(bulk_pH,1,n), 'LineWidth', 2.4, 'LineStyle','-'); ylabel('pH');
ylim([bulk_pH-0.80 bulk_pH+0.20]);       % trace sits ~80 % up the frame
xlabel('hour of the day');
title('What the plant''s two instruments showed: nothing', 'FontWeight','bold');
grid on; box off; xlim([0 23]);

outdir = fullfile(here, '..', 'figs');
if ~isfolder(outdir), mkdir(outdir); end
exportgraphics(f, fullfile(outdir, 'matlab_one_gulf_day.png'), 'Resolution', 160);
fprintf('figure written -> figs/matlab_one_gulf_day.png\n');
