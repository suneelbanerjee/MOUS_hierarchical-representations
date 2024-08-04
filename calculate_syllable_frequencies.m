function transcription = calculate_syllable_frequencies(transcription_path,outpath)
    %%example!
    % transcription_path = "sub-A2055_transcription.csv";
    transcription = readtable(transcription_path);
    phonetics = readtable("dutch_celex_database_updatedv2.xlsx");
    load("syllable_freq_table_new.mat"); % produced by master_table.ipynb

    varNames = syllable_labels;
    %% Initialize a new table to hold the merged columns
    cleanToOriginal = containers.Map('KeyType', 'char', 'ValueType', 'any'); % Explicitly set KeyType to 'char'
    T_new = table();
    Count = syllable_counts;
    
    %% Model syllables independently of stress patterns they take on in a word
    for s = 1:numel(varNames)
        if ischar(varNames{s}) % Check if varNames{s} is a string
            cleanedName = strrep(varNames{s}, '''', '');
            
            %% Debugging statements
            % disp(['cleanedName: ', cleanedName, ' (Type: ', class(cleanedName), ')']);
            % disp(['varNames{s}: ', varNames{s}, ' (Type: ', class(varNames{s}), ')']);
            
            if isKey(cleanToOriginal, cleanedName)
                %% Column with cleanedName already exists, sum the columns
                index = find(cellfun(@(x) strcmp(x, cleanedName), syllable));
                T_new.(cleanedName) = Count(index) + Count(s);
            else
                %% Add to map and copy column to new table
                cleanToOriginal(cleanedName) = varNames{s};
                T_new.(cleanedName) = Count(s);
            end
        else
            %disp(['Skipping non-string varNames{s}: ', num2str(s)]);
        end
    end

    phon_cut = phonetics(:, [3, 4]);
    [~,unique_indices] = unique(phon_cut.Head);
    phon_cut = phon_cut(unique_indices,:);
    %% Source the transcriptions and put them in 'relevant events'
    phon_transcriptions = cell([height(transcription), 1]);
    for m = 1:height(transcription)
        word_idx = strcmp(char(transcription.Transcription(m)), table2cell(phon_cut(:, 1))); 
        word_transc = char(table2cell(phon_cut(word_idx, 2)));
        phon_transcriptions(m) = {word_transc};
    end
    phon_transcriptions = strrep(phon_transcriptions, '"', '');
    phon_transcriptions = strrep(phon_transcriptions, "'", '');

    transcription.Phonetic = phon_transcriptions;
    %% Find the position of the last dot in the file name
    dotIndex = strfind(transcription_path, '.');
    %% Insert '_raw' before the file extension
    rawFileName = insertBefore(transcription_path, dotIndex(end), '_syllabes_raw');

    writetable(transcription,fullfile(outpath,rawFileName))
    %% Filter out all events in the table where no transcription was found
    emptyRows = cellfun(@isempty, transcription.Phonetic) | ismissing(transcription.Phonetic);
    transcription(emptyRows, :) = [];

    %% Different Syllable Frequency metrics
    min_double = [];
    max_double = [];
    mean_double = [];


    rows_missing_full_syllables = [];
    for f = 1:height(transcription)
        indexes = [];
        word = transcription.Phonetic(f);
        word_parts = split(word,"-");
        for i = 1:length(word_parts)
            index = find(strcmp(syllable_labels,transpose(word_parts(i))));
            if isempty(index)
                rows_missing_full_syllables = [rows_missing_full_syllables,f]; %get rid of a row even if only one syllable is missing
                disp(strcat(transcription.Transcription(f), " ", transcription.Phonetic(f)))
            else
            indexes = [indexes,index];
            end
        end
        if ~isempty(indexes)
            word_syllable_frequencies = syllable_counts(indexes);
        end
        %%possible values to use as a parametric regressor
        min_double = [min_double;min(word_syllable_frequencies)];
        max_double = [max_double;max(word_syllable_frequencies)];
        mean_double = [mean_double;mean(word_syllable_frequencies)];
    end
    rows_missing_full_syllables = unique(rows_missing_full_syllables);
    transcription(rows_missing_full_syllables,:) = [];
    min_double(rows_missing_full_syllables) = [];
    max_double(rows_missing_full_syllables) = [];
    mean_double(rows_missing_full_syllables) = [];

    transcription.Minimum_Syllable_Frequency = min_double;
    transcription.Maximum_Syllable_Frequency = max_double;
    transcription.Mean_Syllable_Frequency = mean_double;
    processed_FileName = insertBefore(transcription_path, dotIndex(end), '_syllables_processed');
    writetable(transcription,fullfile(outpath,processed_FileName))
end
