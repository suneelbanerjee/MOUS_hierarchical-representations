function transcription = source_auditory_transcription(events_tsv,outpath)
%Function to obtain onset times and text transcriptions of words
%played in spoken word stimulus files for auditory cohort.
%Takes in the 'events.tsv' file for a single subject and an output path (*.csv) for a single subject (included with MOUS
%dataset) and prints a table containing onset time, word, and other metrics
%from ForcedAligner. Table is returned in 



%Get list of stimulus files played to all subjects
off_on = readtable("MOUS_audio_onset_offsets.xlsx");


subj_audio_files = []; %holds which audio files (number ###.wav) were played for a subject, in order
audio_start_times = []; %the time on master clock when this audio was played
pattern = '\d+(?=.wav)';

%pick out the audio files actually played to a subject
events = tdfread(events_tsv); % for example, 'sub-A2055_task-auditory_events.tsv'
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
%save
writetable(relevant_events,outpath)
transcription = relevant_events;



