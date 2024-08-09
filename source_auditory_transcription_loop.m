addpath('/home/neel/Desktop/MOUS_hierarchical-representations')
source = '/media/neel/MOUS/MOUS/MOUS/SynologyDrive/source'
cd(source)
subjects = dir('sub-A*');
cd('/home/neel/Desktop/MOUS_hierarchical-representations')
for i = 1:length(subjects)
    subject = subjects(i).name
    func = fullfile(source,subject,'func');
    events = fullfile(func,strcat(subject,'_task-auditory_events.tsv'));
    %source_auditory_transcription(events,func)
    transcription = fullfile(func,strcat(subject,'_transcription.csv'));
    calculate_syllable_frequencies(transcription)
end
