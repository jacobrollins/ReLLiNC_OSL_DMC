%epm reading contraction test
clear; clc; close all;
  

data = readmatrix('emg_log_2026-08-11_11-13-49');
channel_list_str = input("channel(s) of interest (seperate each channel by a single space):", 's');
channel_list = sscanf(channel_list_str, '%d').';

% Extract relevant columns from the data matrix

for channel = channel_list
    emg_signal = data(:, (channel + 1));
    emg_signal_volts = (emg_signal./8388607).*(4/6); 
    sample_number = 1:length(emg_signal); %data sampled at 4000hz
    time = sample_number./4000;
    
    
      
    F_s = 4000;                    % sampling frequency
    N = length(emg_signal_volts); % number of samples
    Y = fft(emg_signal_volts);    % FFT of signal
    % Compute single-sided amplitude spectrum
    P2 = abs(Y)./N;               % two-sided spectrum normalized
    P1 = P2(1:floor(N/2)+1);
    if N>1
        P1(2:end-1) = 2*P1(2:end-1);
    end
    f = F_s*(0:floor(N/2))/N;      % frequency vector for single-sided spectrum
    
    %plot spectrum
    figure;
    plot(f, P1);
    xlabel('Frequency (Hz)');
    ylabel('Amplitude (V)');
    title("Single-Sided Amplitude Spectrum of EMG channel " + channel);
    xlim([0 F_s/2]);
    grid on;
    
    %plot adjusted emg
    figure;
    plot(time, emg_signal_volts);
    title("EMG signal channel " + channel)
    xlabel('time (s)')
    ylabel('emg activity (V)')
       
end