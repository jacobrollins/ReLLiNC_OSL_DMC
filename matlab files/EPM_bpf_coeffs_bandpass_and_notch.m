clear; clc; close all; 

fs = 4000;
f_low = 20;
f_high = 450;
order = 2;

% Band-pass filter
[z, p, k] = butter(order, [f_low f_high]/(fs/2), 'bandpass');
sos_bp = zp2sos(z, p, k);

% 60 Hz notch filter
f_notch = 60;
Q = 30;                         % Quality factor 

[b_notch, a_notch] = iirnotch(f_notch/(fs/2), (f_notch/(fs/2))/Q);
sos_notch = tf2sos(b_notch, a_notch);

% Visualize
fvtool(sos_bp, sos_notch, 'Fs', fs);

% Print Teensy initialization
fprintf('\nvoid initFilters() {\n');
fprintf('    for (int i = 0; i < 8; i++) {\n');

% Band-pass 
for i = 1:size(sos_bp,1)
    if i == 1
        name = 'highPass';
    else
        name = 'lowPass';
    end

    fprintf('        // %s\n', name);
    fprintf('        %s[i] = { %.12ff, %.12ff, %.12ff, %.12ff, %.12ff};\n', ...
        name, ...
        sos_bp(i,1), sos_bp(i,2), sos_bp(i,3), ...
        sos_bp(i,5), sos_bp(i,6));
end

% Notch
fprintf('        // 60 Hz notch\n');
fprintf('        notch60[i] = { %.12ff, %.12ff, %.12ff, %.12ff, %.12ff};\n', ...
    sos_notch(1,1), sos_notch(1,2), sos_notch(1,3), ...
    sos_notch(1,5), sos_notch(1,6));

fprintf('    }\n');
fprintf('}\n');