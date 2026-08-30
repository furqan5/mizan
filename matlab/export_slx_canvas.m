function export_slx_canvas()
%EXPORT_SLX_CANVAS  Export the Simulink canvas and the Stateflow chart to PNG.
%
%   Produces two images the report can embed:
%
%     figs/slx_canvas.png     the mizan_plant block diagram as Simulink draws it
%     figs/slx_supervisor.png the Stateflow supervisor chart
%
%   The report already carries a drawn version of the architecture
%   (figs/simulink_model.png, generated from build_mizan_model.m by
%   make_figures.py). That one is for legibility at page size and shows
%   CAUSALITY. This one shows the real block geometry, which is the evidence
%   that the model exists and is what the build script says it is. They are
%   complementary and the report uses both.
%
%   Run:  export_slx_canvas
%
%   Requires: Simulink, Stateflow. If mizan_plant.slx is missing it is
%   rebuilt from build_mizan_model.m first, so this is safe to run cold.

mdl  = 'mizan_plant';
here = fileparts(mfilename('fullpath'));
figs = fullfile(here, '..', 'figs');
if ~isfolder(figs), mkdir(figs); end

% ---------------------------------------------------------------- build ---
slx = fullfile(here, [mdl '.slx']);
if ~isfile(slx)
    fprintf('%s.slx not found -- building it from build_mizan_model.m\n', mdl);
    build_mizan_model();
end

bdclose('all');
load_system(slx);

% Arrange once so the exported canvas is tidy rather than however it was
% last left by hand. This is cosmetic and changes no behaviour.
try
    Simulink.BlockDiagram.arrangeSystem(mdl);
catch
    % arrangeSystem is not available in every release; the canvas still
    % exports, it is just laid out as saved.
end

open_system(mdl);

% ------------------------------------------------------- canvas to PNG ---
out1 = fullfile(figs, 'slx_canvas.png');
ok1 = false;
try
    % The reliable route across releases: print the system by name.
    print(['-s' mdl], '-dpng', '-r200', out1);
    ok1 = isfile(out1);
catch ME
    fprintf('print() route failed: %s\n', ME.message);
end
if ~ok1
    try
        saveas(get_param(mdl, 'Handle'), out1, 'png');
        ok1 = isfile(out1);
    catch ME
        fprintf('saveas() route failed: %s\n', ME.message);
    end
end
if ok1
    fprintf('written -> figs/slx_canvas.png\n');
else
    fprintf('COULD NOT export the canvas. Report this rather than guessing.\n');
end

% -------------------------------------------- Stateflow chart to PNG ----
out2 = fullfile(figs, 'slx_supervisor.png');
ok2 = false;
chart = [mdl '/Supervisor'];
try
    if getSimulinkBlockHandle(chart) > 0
        sfprint(chart, 'png', out2, 'view');
        % sfprint appends its own extension in some releases
        if ~isfile(out2) && isfile([out2 '.png'])
            movefile([out2 '.png'], out2);
        end
        ok2 = isfile(out2);
    else
        fprintf('no block at %s -- skipping the chart export\n', chart);
    end
catch ME
    fprintf('sfprint failed: %s\n', ME.message);
end
if ok2
    fprintf('written -> figs/slx_supervisor.png\n');
end

% --------------------------------------------------------------- report --
fprintf('\nBlocks in %s:\n', mdl);
b = find_system(mdl, 'SearchDepth', 1, 'Type', 'Block');
for k = 1:numel(b)
    fprintf('   %s\n', get_param(b{k}, 'Name'));
end
fprintf('\n%d top-level blocks, %d signal lines.\n', numel(b), ...
        numel(find_system(mdl, 'SearchDepth', 1, 'FindAll', 'on', 'Type', 'line')));

close_system(mdl, 0);
end
