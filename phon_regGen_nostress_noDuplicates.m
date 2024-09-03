%Get list of words shown to subjects
off_on = readtable("MOUS_audio_onset_offsets.xlsx");
phonetics = readtable("dutch_celex_database_updated.xlsx");
load("syllable_freq_table.mat")
% Get existing variable names
varNames = T.Properties.VariableNames;

% Initialize a map to hold the mapping of cleaned names to original names
cleanToOriginal = containers.Map();

% Initialize a new table to hold the merged columns
T_new = table();

for s = 1:numel(varNames)
    cleanedName = strrep(varNames{s}, '''', '');
    
    if isKey(cleanToOriginal, cleanedName)
        % Column with cleanedName already exists, sum the columns
        T_new.(cleanedName) = T.(cleanedName) + T.(varNames{s});
    else
        % Add to map and copy column to new table
        cleanToOriginal(cleanedName) = varNames{s};
        T_new.(cleanedName) = T.(varNames{s});
    end
end
phon_cut = phonetics(:,[3,4]);
subj_audio_files = []; %holds which audio files (number ###.wav) were played for a subject, in order
audio_start_times = []; %the time on master clock when this audio was played
pattern = '\d+(?=.wav)';
%for i = 1:length subjects
%cd subject path

%pick out the audio files
events = tdfread('sub-A2055_task-auditory_events.tsv');
for j = 1:length(string(events.type))
    if strtrim(string(events.type(j,:))) == "Sound"
        filename = events.value(j,:);
        result = regexp(filename, pattern, 'match');
        if ~isempty(result)
            extracted_number = result{1};
        else
            extracted_number = 'No match found';
        end
        subj_audio_files = [subj_audio_files; str2num(extracted_number)];
        audio_start_times = [audio_start_times;(events.onset(j))];
    end
end

%find the words and start times
relevant_events = table();
for k = 1:length(subj_audio_files)
    % Regular expression pattern
    TGpattern = strcat(num2str(subj_audio_files(k)), '(?=.TextGrid)');
    % Apply the regular expression to each element in the cell array
    matchIndices = cellfun(@(x) ~isempty(regexp(x, TGpattern, 'once')), table2cell(off_on(:,'TextGrid')));
    % Find the indices of the matches
    matchingRowIndices = find(matchIndices);
    segment = off_on(matchingRowIndices,[4,5,9,10]);
    segment.AlignOnset = segment.AlignOnset + audio_start_times(k); %aligns the onset times with the master clock
    relevant_events = vertcat(relevant_events,segment);
end



%source the transcriptions and put them in 'relevant events'
phon_transcriptions = cell([height(relevant_events),1]);
for m = 1:height(relevant_events)
    word_idx = find(strcmp(char(relevant_events.Transcription(m)), table2cell(phon_cut(:,1))), 1, 'first');
    word_transc = char(table2cell(phon_cut(word_idx, 2)));
    phon_transcriptions(m) = {word_transc};
end
phon_transcriptions = strrep(phon_transcriptions, '"', '');
phon_transcriptions = strrep(phon_transcriptions, "'", '');

relevant_events.Phonetic = phon_transcriptions;

%filter out all events in the table where no transcription was found
emptyRows = cellfun(@isempty, relevant_events.Phonetic) | ismissing(relevant_events.Phonetic);

% Delete those rows from the table
relevant_events(emptyRows, :) = [];


%Frequency metrics!
    min_double = [];
    max_double = [];
    mean_double = [];
    first_double = [];
    last_double = [];
for f = 1:height(relevant_events)
    syllables = strsplit(relevant_events.Phonetic(f),'-');
    frequencies = cell([length(syllables),1]);
    for ff = 1:length(syllables)
        try
            frequencies(ff) = table2cell(T_new(1,syllables(ff)));
        catch
            frequencies(ff) = {strcat(relevant_events.Phonetic(f)," ",num2str(ff)," position not found")}; %happens strangely often...
            disp(relevant_events.Phonetic(f))
            %display offending syllable
        end
    end
    freqs_double = [];
    
    for fff = 1:length(frequencies)
        freqs_double = [freqs_double;str2double(frequencies{fff,1})];
    end
    %minimum
    minFreq = min(freqs_double);
    min_double = [min_double;minFreq];
    %maximum
    maxFreq = max(freqs_double);
    max_double = [max_double; maxFreq];
    %mean
    meanFreq = mean(freqs_double);
    mean_double = [mean_double;meanFreq];
    %log minimum

    %log maximum

    %log mean

    %dmMin

    %dmMax

    %dmMean

    %dmLogMin

    %dmLogMax

    %dmLogMean

    %first
    first = freqs_double(1);
    first_double = [first_double;first];
    %last
    last = freqs_double(length(freqs_double));
    last_double = [last_double;last];
    %logFirst

    %logLast

    %dmFirst

    %dmLast

    %dmLogFirst

    %dmLogLast


end

%add the values to relevant events. calculate dM and log. 

relevant_events.Minimum = num2cell(min_double);
relevant_events.Maximum = num2cell(max_double);
relevant_events.Mean = num2cell(mean_double);
relevant_events.First = num2cell(first_double);
relevant_events.Last = num2cell(last_double);
relevant_events.logMinimum = num2cell(log(min_double));
relevant_events.logMaximum = num2cell(log(max_double));
relevant_events.logMean = num2cell(log(mean_double));
relevant_events.logFirst = num2cell(log(first_double));
relevant_events.logLast = num2cell(log(last_double));

relevant_events.dmMinimum = num2cell(min_double - mean(min_double));
relevant_events.dmMaximum = num2cell(max_double - mean(max_double));
relevant_events.dmMean = num2cell(mean_double - mean(mean_double));
relevant_events.dmFirst = num2cell(first_double - mean(first(double)));
relevant_events.dmLast = num2cell(last_double- mean(last_double));
relevant_events.dmlogMinimum = num2cell(log(min_double) - mean(log(min_double)));
relevant_events.dmlogMaximum = num2cell(log(max_double) - mean(log(max_double)));
relevant_events.dmlogMean = num2cell(log(mean_double) - mean(log(mean_double)));
relevant_events.dmlogFirst = num2cell(log(first_double) - mean(log(first_double)));
relevant_events.dmlogLast = num2cell(log(last_double) - mean(log(last_double)));

%cd to subject's source directory
tablename = %subject + "phon_freqRegresors"
writetable(relevant_events,tablename)

%end





