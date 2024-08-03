function syllable_frequencies = calculate_syllable_frequencies(transcription,outpath)
transcription = readtable(transcription);
phonetics = readtable("dutch_celex_database_updated.xlsx");
%load("syllable_freq_table_new.mat") %produced by master_table.ipynb


varNames = syllable;
% Initialize a new table to hold the merged columns
T_new = table();

%model syllables independently of stress patterns they take on in a word
for s = 1:numel(varNames)
    cleanedName = strrep(varNames{s}, '''', '');
    
    if isKey(cleanToOriginal, cleanedName)
        % Column with cleanedName already exists, sum the columns
        index = find(cellfun(@(x) strcmp(x, cleanedName), syllable));
        T_new.(cleanedName) = Count(index) + Count(s);
    else
        % Add to map and copy column to new table
        cleanToOriginal(cleanedName) = varNames{s};
        T_new.(cleanedName) = Count(s);
    end
end
phon_cut = phonetics(:,[3,4]);



%source the transcriptions and put them in 'relevant events'
phon_transcriptions = cell([height(transcription),1]);
for m = 1:height(transcription)
    word_idx = strcmp(char(transcription.Transcription(m)),table2cell(phon_cut(:,1))); %can perhaps source these from a variable from the previous project-- all the existing 'subtlex' transcriptions
    word_transc = char(table2cell(phon_cut(word_idx,2)));
    phon_transcriptions(m) = {word_transc};
end
phon_transcriptions = strrep(phon_transcriptions, '"', '');
phon_transcriptions = strrep(phon_transcriptions, "'", '');

transcription.Phonetic = phon_transcriptions;

%filter out all events in the table where no transcription was found
emptyRows = cellfun(@isempty, transcription.Phonetic) | ismissing(transcription.Phonetic);

% Delete those rows from the table
transcription(emptyRows, :) = [];


%Frequency metrics!
    min_double = [];
    max_double = [];
    mean_double = [];
    first_double = [];
    last_double = [];
for f = 1:height(transcription)
    syllables = strsplit(transcription.Phonetic(f),'-');
    frequencies = cell([length(syllables),1]);
    for ff = 1:length(syllables)
        try
            frequencies(ff) = table2cell(T_new(1,syllables(ff)));
        catch
            frequencies(ff) = {strcat(transcription.Phonetic(f)," ",num2str(ff)," position not found")}; %happens strangely often...
            disp(transcription.Phonetic(f))
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



