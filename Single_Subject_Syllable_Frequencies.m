function syllable_frequencies = calculate_syllable_frequency()
%source the transcriptions and put them in 'relevant events'
phon_transcriptions = cell([height(relevant_events),1]);
for m = 1:height(relevant_events)
    word_idx = find(strcmp(char(relevant_events.Transcription(m)),table2cell(phon_cut(:,1)))); %can perhaps source these from a variable from the previous project-- all the existing 'subtlex' transcriptions
    word_transc = char(table2cell(phon_cut(word_idx,2)));
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



