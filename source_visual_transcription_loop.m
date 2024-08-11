source = '/media/neel/MOUS/MOUS/MOUS/SynologyDrive/source'
cd(source)
subjects = dir('sub-V*')

cd('/home/neel/Desktop/MOUS_hierarchical-representations')
for i = 1:length(subjects)  
    subject = subjects(i).name
    func = fullfile(source,subject,'func');
    events = fullfile(func,strcat(subject,'_task-visual_events.tsv'));
%     onsetTimes = tdfread(events, '\t'); % Read events.tsv file
%     onsetTimes.type = string(onsetTimes.type); % Convert char array to string array, to make logical comparisons easier
%     onsetTimes.value = string(onsetTimes.value);
    
%     wordonsets = []; % stores onset + words to return in excel sheet

%     for k = 1:length(onsetTimes.onset) %for every line in the events file...
%         if strtrim(onsetTimes.type(k,:)) == 'Picture' %type = Picture only
%             if strtrim(onsetTimes.value(k,:)) == 'blank' %do nothing if Picture value *equals* blank, ISI(interstim interval), or WOORDEN (wordlist)
%             elseif strtrim(onsetTimes.value(k,:)) == 'ISI'
%             elseif strtrim(onsetTimes.value(k,:)) == 'WOORDEN'
%             elseif contains(onsetTimes.value(k,:), 'FIX') %do nothing if Picture value *contains* FIX, QUESTION, or ZINNEN (sentence)
%             elseif contains(onsetTimes.value(k,:), 'ZINNEN')
%             elseif contains(onsetTimes.value(k,:), 'QUESTION')
%             else %since the values contain numbers, spaces, and punctuation, we need to remove them:
%                 word = onsetTimes.value(k,:);
%                 word = erase(word, '.'); %remove periods from value
%                 word = strrep(word, ' ', ''); %remove spaces from value
%                 word = lower(word); %convert to lowercase
%                 word = regexp(word,'[^\d_\.]*','match'); %remove numbers from value; now value = only the word.
%                 time = num2str(onsetTimes.onset(k));
%                 % frequency = WordFreq.Lg10WF(strcmp(WordFreq.Word, word));
%                 % if ~isempty(frequency)
%                 %     wordonsets = [wordonsets; onsetTimes.onset(k,:) word 0 frequency]; %add onsetTime and word to wordonsets
%                 % end
%                 wordonsets = [wordonsets; [{time}, {word}]];
%             end
%         end
%     end
% transcription = array2table(wordonsets, 'VariableNames', {'Onset', 'Word'});
% % Specify the filename for the CSV file
    outputFileName = fullfile(source, subject, 'func', strcat(subject, '_transcription.csv'));
    source_visual_transcription(events, outputFileName)
end

