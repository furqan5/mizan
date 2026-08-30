function build_mizan_model()
%BUILD_MIZAN_MODEL  Construct mizan_plant.slx from scratch, programmatically.
%
%   The model is built by this script rather than shipped as a binary .slx,
%   so every block, parameter and connection is reviewable as text and sits
%   under version control. Run it once; it writes matlab/mizan_plant.slx.
%
%   WHAT THE MODEL IS
%
%   A condenser-water loop with a supervisory controller on top of it.
%
%     ambient + cooling load  (one Dhahran summer day)
%              |
%     +--------v-----------------+   the tower's capability, from the
%     |  COOLING TOWER  (Poppe)  |   validated heat-and-mass-transfer
%     |  MATLAB Function block   |   model, expressed as a conductance
%     +--------+-----------------+
%              |
%     +--------v-----------------------------+  the loop's thermal INERTIA
%     |  LOOP THERMAL MASS  (Simscape)       |  as a physical network:
%     |  thermal mass = 25 t of loop water   |  a mass, a heat source and
%     |  heat source  = condenser duty       |  a convective path. This is
%     |  convection   = the tower            |  what makes it a control
%     +--------+-----------------------------+  problem, not arithmetic.
%              |
%     +--------v---------+   +---------------------------+
%     | CHILLER          |   | SCALING LIMIT AT THE SKIN |
%     | named York YT    |   | brucite saturation pH     |
%     +--------+---------+   +------------+--------------+
%              |                          |
%              +------------+-------------+
%                           |
%                  +--------v--------------+
%                  | SUPERVISOR (Stateflow)|  shadow -> advisory -> closed
%                  +-----------------------+  loop, with a hard fallback
%
%   WHY SIMSCAPE IS HERE AND NOT JUST MORE MATLAB
%
%   The Poppe model is steady-state: given conditions, what does the tower
%   do. A real loop holds tonnes of water and takes minutes to respond, and
%   a controller that ignores that will hunt. The Simscape network carries
%   that inertia as a physical network, so the time constant is the loop's
%   real thermal mass over its real conductance rather than a number
%   somebody chose.
%
%   Requires: Simulink, Simscape, Stateflow.

mdl = 'mizan_plant';
here = fileparts(mfilename('fullpath'));
bdclose('all');
new_system(mdl);

% A fixed-step EXPLICIT solver at the control interval. Three reasons:
%
%   1. The shipped controller runs on an edge device with a control
%      interval to meet, so the model should be solved the way the device
%      will solve it -- one step, bounded work, no adaptive back-tracking.
%   2. The physical network here is a single thermal mass. It is not stiff,
%      so an implicit solver buys nothing.
%   3. It buys a great deal of time. An implicit solver calls the Poppe
%      integrator several times per step while it iterates, and a 24-hour
%      run took over half an hour of CPU before it was abandoned.
set_param(mdl, 'StopTime', '86400');      % one day, in seconds
set_param(mdl, 'SolverType', 'Fixed-step');
set_param(mdl, 'Solver', 'ode1');         % explicit Euler at the control step
set_param(mdl, 'FixedStep', '60');        % a one-minute control interval

B = @(lib, nm, pos, varargin) add_block(lib, [mdl '/' nm], ...
                                        'Position', pos, varargin{:});

% ---------------------------------------------------------------------
% blocks
% ---------------------------------------------------------------------
B('simulink/Sources/Clock', 'Clock', [30 40 60 70]);

B('simulink/User-Defined Functions/MATLAB Function', 'Ambient and load', ...
  [130 20 290 90]);
setFcn(mdl, 'Ambient and load', [
"function [T_db, rh, Q_evap] = fcn(t)"
"% One Dhahran summer day: cool before dawn, brutal in the afternoon, with"
"% the cooling load following the heat as it does in every real plant."
"hr = mod(t/3600, 24);"
"s  = sin(pi*max(hr-6,0)/16)^2;"
"T_db   = 32 + 12*s;              % 32 C at night, 44 C at peak"
"rh     = 0.55 - 0.25*s;          % drier as it heats"
"Q_evap = 10000*(0.62 + 0.38*s);  % kW of cooling delivered"
]);

B('simulink/User-Defined Functions/MATLAB Function', 'Cooling tower', ...
  [370 120 530 210]);
setFcn(mdl, 'Cooling tower', [
"function [T_cold, m_evap, UA, T_wb] = fcn(T_hot, T_db, rh, fan_pct)"
"% The tower, from the validated Poppe heat-and-mass-transfer model."
"% Returns the cold water it can reach, the evaporation rate, an"
"% equivalent conductance UA [kW/K] for the physical network, and the"
"% wet-bulb -- the coldest temperature the tower could ever reach."
"coder.extrinsic('mizan_tower_step');"
"T_cold = 30; m_evap = 0; UA = 100; T_wb = 25;"
"[T_cold, m_evap, UA, T_wb] = mizan_tower_step(T_hot, T_db, rh, fan_pct);"
]);

B('simulink/User-Defined Functions/MATLAB Function', 'Chiller', ...
  [600 120 760 210]);
setFcn(mdl, 'Chiller', [
"function [P_chiller, Q_cond, in_env] = fcn(Q_evap, T_cold)"
"% Electrical power drawn by the chiller, and the heat the tower must"
"% therefore reject: the cooling load PLUS the compressor work."
"%"
"% IN_ENV is 0 when entering condenser water leaves the range the"
"% manufacturer's curves were fitted in. Left unchecked an optimiser walks"
"% out of that range and collects a saving that does not exist. This one"
"% did exactly that once, and booked a false water saving on the strength"
"% of it."
"coder.extrinsic('mizan_chiller_step');"
"P_chiller = 1500; in_env = 1;"
"[P_chiller, in_env] = mizan_chiller_step(Q_evap, T_cold);"
"Q_cond = Q_evap + P_chiller;"
]);

buildThermalNetwork(mdl, 830, 120);

B('simulink/User-Defined Functions/MATLAB Function', 'Scaling limit', ...
  [370 320 530 410]);
setFcn(mdl, 'Scaling limit', [
"function [pH_limit, margin, T_skin] = fcn(T_hot, cycles, bulk_pH)"
"% The pH above which magnesium silicate deposits, evaluated at the"
"% CONDENSER TUBE SKIN rather than in the bulk water."
"%"
"% Brucite's saturation pH is RETROGRADE -- it falls as the surface gets"
"% hotter -- so the same loop is safe at low load and depositing at high"
"% load, with pH and conductivity reading identical in both cases. No"
"% fixed setpoint can express that."
"coder.extrinsic('mizan_chem_step');"
"pH_limit = 9; T_skin = 40;"
"[pH_limit, T_skin] = mizan_chem_step(T_hot, cycles);"
"% An extrinsic call is opaque to the compiler, so the result is forced"
"% real and finite here. The chemistry can legitimately return an infinite"
"% limit when there is no magnesium in the water, and a solver transient"
"% can briefly ask for a temperature no water reaches."
"pH_limit = real(pH_limit);"
"if ~isfinite(pH_limit), pH_limit = 14; end"
"T_skin   = real(T_skin);"
"margin = pH_limit - bulk_pH;   % positive = safe, negative = depositing"
]);

B('simulink/User-Defined Functions/MATLAB Function', 'Condenser', ...
  [830 20 990 100]);
setFcn(mdl, 'Condenser', [
"function T_hot = fcn(T_basin, Q_cond)"
"% Water leaves the tower basin cold, picks up the condenser duty, and"
"% arrives back at the top of the tower hot:"
"%"
"%     T_hot = T_basin + Q_cond / (m_w * cp)"
"%"
"% That temperature rise is the condenser RANGE, and it is what sets the"
"% tube skin temperature -- which is where the scale actually forms."
"m_w = 478;  cp = 4.186;"
"T_hot = T_basin + Q_cond/(m_w*cp);"
]);

B('simulink/User-Defined Functions/MATLAB Function', 'Basin heat balance', ...
  [830 560 990 640]);
setFcn(mdl, 'Basin heat balance', [
"function Q_net = fcn(T_target, T_basin)"
"% The tower basin is a mixing volume. Water arrives in it at whatever"
"% temperature the tower managed to reach, at the circulating flow rate,"
"% and the basin's own temperature relaxes towards that:"
"%"
"%     M cp dT/dt = m_w cp (T_target - T_basin)"
"%"
"% The time constant is the basin inventory over the circulating flow --"
"% about five minutes here -- and it is the reason a condenser loop cannot"
"% be controlled as though it responded instantly."
"m_w = 478;  cp = 4.186;"
"Q_net = m_w*cp*(T_target - T_basin);"
]);

buildSupervisor(mdl, 620, 330);

B('simulink/Sources/Constant', 'cycles',    [230 330 300 360], 'Value', '4');
B('simulink/Sources/Constant', 'bulk pH',   [230 380 300 410], 'Value', '8.7');
B('simulink/Sources/Constant', 'sensor ok', [230 430 300 460], 'Value', '1');

B('simulink/User-Defined Functions/MATLAB Function', 'Fan power', ...
  [620 480 760 550]);
setFcn(mdl, 'Fan power', [
"function P_fan = fcn(fan_pct)"
"% Fan shaft power by the affinity law -- power goes as the CUBE of air"
"% flow, which is why backing the fan off is the single biggest lever the"
"% controller has on tower energy."
"P_fan = 110*(max(min(fan_pct,100),0)/100)^3;"
]);

% The controller acts on the PREVIOUS measurement, never on one it is
% causing in the same instant. Without this the model contains an algebraic
% loop -- and so would a real controller that pretended to be instantaneous.
% One step is the 60 s control interval.
B('simulink/Discrete/Memory', 'Control interval delay', ...
  [420 480 480 520], 'InitialCondition', '85');

% The basin temperature is a MEASUREMENT, and a measurement is of the
% previous control interval. Reading it as though it were simultaneous with
% the heat balance it drives makes the whole plant one algebraic loop --
% which is Simulink pointing out that an instantaneous sensor does not
% exist. One 60 s step of delay is both the fix and the truth.
B('simulink/Discrete/Memory', 'Basin temperature (measured)', ...
  [1010 300 1090 340], 'InitialCondition', '26.85');   % = the Simscape
                                                       % mass default, 300 K

B('simulink/Math Operations/Gain', 'seconds to hours', ...
  [230 490 300 520], 'Gain', '1/3600');

outs = {'T_cold','T_hot','T_skin','pH_limit','margin', ...
        'P_chiller','P_fan','fan_cmd','mode','in_env', ...
        'T_target','Q_net'};
for i = 1:numel(outs)
    B('simulink/Sinks/To Workspace', outs{i}, ...
      [1120 40+45*i 1210 75+45*i], ...
      'VariableName', outs{i}, 'SaveFormat', 'Timeseries', ...
      'MaxDataPoints', 'inf');
end

% ---------------------------------------------------------------------
% wiring, written out explicitly rather than auto-routed, because the
% connections ARE the model and a reviewer has to be able to check them
% ---------------------------------------------------------------------
L = @(a, ap, b, bp) add_line(mdl, sprintf('%s/%d', a, ap), ...
                             sprintf('%s/%d', b, bp), 'autorouting', 'on');

L('Clock', 1, 'Ambient and load', 1);
L('Ambient and load', 1, 'Cooling tower', 2);      % T_db
L('Ambient and load', 2, 'Cooling tower', 3);      % rh
L('Ambient and load', 3, 'Chiller', 1);            % Q_evap

L('Supervisor', 1, 'Control interval delay', 1);
L('Control interval delay', 1, 'Cooling tower', 4);   % fan command, delayed

% The STATE is the basin temperature -- the coldest water in the loop.
% Everything else is worked out from it, in the order the water flows.
L('Loop thermal mass', 1, 'Basin temperature (measured)', 1);
L('Basin temperature (measured)', 1, 'Chiller', 2);   % basin -> condenser
L('Basin temperature (measured)', 1, 'Condenser', 1);
L('Chiller', 2, 'Condenser', 2);                   % Q_cond
L('Condenser', 1, 'Cooling tower', 1);             % hot water to the tower
L('Cooling tower', 1, 'Basin heat balance', 1);    % what the tower reached
L('Basin temperature (measured)', 1, 'Basin heat balance', 2);
L('Basin heat balance', 1, 'Loop thermal mass', 1);

L('Condenser', 1, 'Scaling limit', 1);             % T_hot sets the skin
L('cycles', 1, 'Scaling limit', 2);
L('bulk pH', 1, 'Scaling limit', 3);

L('Scaling limit', 2, 'Supervisor', 1);            % margin
L('Chiller', 3, 'Supervisor', 2);                  % in_env
L('sensor ok', 1, 'Supervisor', 3);
L('Clock', 1, 'seconds to hours', 1);
L('seconds to hours', 1, 'Supervisor', 4);         % hours_run

L('Control interval delay', 1, 'Fan power', 1);

L('Basin temperature (measured)', 1, 'T_cold', 1);
L('Condenser', 1, 'T_hot', 1);
L('Scaling limit', 3, 'T_skin', 1);
L('Scaling limit', 1, 'pH_limit', 1);
L('Scaling limit', 2, 'margin', 1);
L('Chiller', 1, 'P_chiller', 1);
L('Fan power', 1, 'P_fan', 1);
L('Control interval delay', 1, 'fan_cmd', 1);
L('Supervisor', 2, 'mode', 1);
L('Chiller', 3, 'in_env', 1);
L('Cooling tower', 1, 'T_target', 1);
L('Basin heat balance', 1, 'Q_net', 1);

Simulink.BlockDiagram.arrangeSystem(mdl);
save_system(mdl, fullfile(here, [mdl '.slx']));
close_system(mdl, 0);
fprintf('written -> matlab/%s.slx\n', mdl);
end


% =====================================================================
function setFcn(mdl, blkname, lines)
%SETFCN  Put MATLAB code into a MATLAB Function block.
    st = sfroot();
    obj = st.find('-isa', 'Stateflow.EMChart', '-and', ...
                  'Path', [mdl '/' blkname]);
    obj.Script = strjoin(cellstr(lines), newline);
end


function buildThermalNetwork(mdl, x, y)
%BUILDTHERMALNETWORK  The condenser loop's thermal inertia, as a real
%   Simscape physical network rather than a transfer function.
%
%   The whole thing is one sentence of physics:
%
%       the loop water heats up when more heat goes into it than comes out
%
%   heat in   = the condenser duty (cooling load plus compressor work)
%   heat out  = what the tower manages to reject
%   the mass  = 150 tonnes of water in the basin and the loop
%
%   That mass is why a condenser loop takes minutes rather than seconds to
%   settle, and it is the reason this is a control problem at all. Model it
%   as a physical network and the time constant is the real mass over the
%   real conductance; guess a first-order lag instead and it is whatever
%   number you chose.
%
%   Blocks used are all base Simscape Foundation -- no Simscape Fluids,
%   which does not check out on this machine.
    sub = [mdl '/Loop thermal mass'];
    add_block('built-in/Subsystem', sub, 'Position', [x y x+200 y+120]);
    for b = {'In1','Out1'}
        h = getSimulinkBlockHandle([sub '/' b{1}]);
        if h > 0, delete_block(h); end
    end

    add_block('simulink/Sources/In1', [sub '/Q_net_kW'], 'Position', [20 100 40 120]);
    add_block('simulink/Sinks/Out1',  [sub '/T_loop'],   'Position', [560 200 580 220]);

    add_block('simulink/Math Operations/Gain', [sub '/kW to W'], ...
              'Position', [70 95 110 125], 'Gain', '1000');
    add_block('nesl_utility/Simulink-PS Converter', [sub '/QPS'], ...
              'Position', [150 95 180 125]);
    add_block('nesl_utility/PS-Simulink Converter', [sub '/TPS'], ...
              'Position', [480 195 510 225]);
    % Simscape thermal ports are in KELVIN. The first run of this model read
    % the sensor as Celsius, so the chemistry was asked for the saturation
    % pH at 341 C and the chiller was told its condenser water was at 330 C.
    % Both refused -- the chemistry clamped and the chiller reported itself
    % out of envelope for the entire day -- which is how the error was found
    % within one run. It is the fourth unit defect in this project and the
    % fourth caught the same way: by a physical model declining to produce a
    % plausible-looking wrong answer. The conversion is an explicit block
    % rather than a converter setting so that it is visible in the diagram.
    add_block('simulink/Math Operations/Bias', [sub '/K to degC'], ...
              'Position', [530 195 560 225], 'Bias', '-273.15');

    % The physical network gets its OWN fixed-step local solver, rather than
    % being stepped by Simulink's. Two reasons, and the second is the one
    % that matters:
    %
    %   1. It is how the shipped controller will run. An edge device solves
    %      one step of bounded work per control interval; it does not
    %      back-track adaptively.
    %   2. Without it the run diverged. The identical arithmetic, written
    %      as a plain MATLAB loop, is stable over the full day and settles
    %      at 28-32 C. That difference was the solver configuration, not the
    %      physics -- which is worth knowing before trusting any result the
    %      model produces.
    add_block('nesl_utility/Solver Configuration', [sub '/Solver'], ...
              'Position', [150 320 190 360], ...
              'UseLocalSolver', 'on', ...
              'LocalSolverChoice', 'NE_BACKWARD_EULER_ADVANCER', ...
              'LocalSolverSampleTime', '60');
    add_block('fl_lib/Thermal/Thermal Sources/Ideal Heat Flow Source', ...
              [sub '/Net heat into the loop'], 'Position', [230 130 290 190]);
    add_block('fl_lib/Thermal/Thermal Elements/Thermal Mass', ...
              [sub '/Basin water  (150 t)'], 'Position', [360 110 420 170], ...
              'mass', '1.5e5', 'sp_heat', '4186');
    % The block ignores an initial temperature passed this way -- it keeps
    % its default 300 K (26.85 C), which was confirmed by reading it back.
    % Rather than fight it, the model simply starts there. 26.85 C is a
    % plausible basin temperature, and a 24-hour run settles to its own
    % equilibrium inside the first hour regardless of where it starts.
    % What DOES matter is that the measurement delay's initial value agrees
    % with it, or the first step is inconsistent with the state.
    add_block('fl_lib/Thermal/Thermal Sensors/Ideal Temperature Sensor', ...
              [sub '/Loop temperature'], 'Position', [360 220 420 280]);
    add_block('fl_lib/Thermal/Thermal Elements/Thermal Reference', ...
              [sub '/Reference'], 'Position', [230 320 260 350]);
    add_block('fl_lib/Thermal/Thermal Elements/Thermal Reference', ...
              [sub '/Reference 2'], 'Position', [470 320 500 350]);

    % Port indices differ between the source and the sensor, which is the
    % kind of thing that is worth writing down once:
    %   Ideal Heat Flow Source   LConn1 = A, RConn1 = signal S, RConn2 = B
    %   Ideal Temperature Sensor LConn1 = A, RConn1 = B,        RConn2 = signal
    % Simscape refuses a wrong connection outright rather than accepting it
    % and producing nonsense, which is exactly the property we want.
    add_line(sub, 'Q_net_kW/1', 'kW to W/1');
    add_line(sub, 'kW to W/1', 'QPS/1');
    add_line(sub, 'QPS/RConn1', 'Net heat into the loop/RConn1');    % signal S
    % SIGN. Positive heat flows from port B to port A on this block, not
    % the other way round, so port A goes to the water and port B to the
    % reference. With them swapped, +1000 kW into a 150 t mass for 600 s
    % gave -0.956 K instead of +0.956 K -- the right magnitude and the wrong
    % direction, which is the signature of a sign convention rather than a
    % physics error. It was found by pushing a known heat flow into a known
    % mass and checking the answer against arithmetic, which is the only
    % reliable way to settle a sign.
    add_line(sub, 'Net heat into the loop/LConn1', 'Basin water  (150 t)/LConn1');
    add_line(sub, 'Net heat into the loop/RConn2', 'Reference/LConn1');
    add_line(sub, 'Basin water  (150 t)/LConn1', 'Loop temperature/LConn1');
    add_line(sub, 'Loop temperature/RConn1', 'Reference 2/LConn1');
    add_line(sub, 'Loop temperature/RConn2', 'TPS/LConn1');
    add_line(sub, 'TPS/1', 'K to degC/1');
    add_line(sub, 'K to degC/1', 'T_loop/1');
    add_line(sub, 'Solver/RConn1', 'Reference/LConn1');
end


function buildSupervisor(mdl, x, y)
%BUILDSUPERVISOR  The Stateflow chart that decides how much authority the
%   controller is allowed to have.
%
%   The product ships READ-ONLY. It earns write access one actuator at a
%   time, and hands that authority straight back the moment anything is
%   wrong. That is a commercial decision as much as a safety one: it is the
%   shortest route through a plant's operational-technology security review,
%   because for the first eight weeks the device provably cannot touch
%   anything.
    ch = [mdl '/Supervisor'];
    load_system('sflib');
    add_block('sflib/Chart', ch, 'Position', [x y x+220 y+120]);

    st = sfroot();
    chart = st.find('-isa', 'Stateflow.Chart', '-and', 'Path', ch);
    chart.ActionLanguage = 'MATLAB';

    for nm = {'margin','in_env','sensor_ok','hours_run'}
        d = Stateflow.Data(chart); d.Name = nm{1}; d.Scope = 'Input';
    end
    for nm = {'fan_cmd','mode'}
        d = Stateflow.Data(chart); d.Name = nm{1}; d.Scope = 'Output';
    end

    s1 = mkState(chart, [40  40 220 80], 'SHADOW', ...
        sprintf('du:\nmode = 1;\nfan_cmd = 85;'));
    s2 = mkState(chart, [40 160 220 80], 'ADVISORY', ...
        sprintf('du:\nmode = 2;\nfan_cmd = 85;'));
    s3 = mkState(chart, [40 280 220 90], 'CLOSED_LOOP', ...
        sprintf('du:\nmode = 3;\nfan_cmd = 85 - 25*tanh(max(-margin,0)*8);'));
    s4 = mkState(chart, [330 160 220 80], 'FALLBACK', ...
        sprintf('du:\nmode = 0;\nfan_cmd = 85;'));

    mkTrans(chart, s1, s2, 'hours_run > 1344');   % eight weeks read-only
    mkTrans(chart, s2, s3, 'hours_run > 1512');   % one week after sign-off
    mkTrans(chart, s3, s4, '~sensor_ok || ~in_env');
    mkTrans(chart, s2, s4, '~sensor_ok');
    mkTrans(chart, s4, s2, 'sensor_ok && in_env');

    t = Stateflow.Transition(chart);
    t.Destination = s1;
    t.DestinationOClock = 0;
    t.SourceEndpoint = [s1.Position(1)+30, s1.Position(2)-40];
    t.MidPoint       = [s1.Position(1)+30, s1.Position(2)-20];
end


function s = mkState(chart, pos, nm, act)
    s = Stateflow.State(chart);
    s.Position = pos;
    s.LabelString = sprintf('%s\n%s', nm, act);
end

function t = mkTrans(chart, src, dst, cond)
    t = Stateflow.Transition(chart);
    t.Source = src; t.Destination = dst;
    t.LabelString = sprintf('[%s]', cond);
end
