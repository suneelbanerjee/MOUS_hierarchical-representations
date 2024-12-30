function V = generate_cluster_masks(spm_path, threshold, extent)

    %spm = Your group-level SPM.mat file.
    %threshold = pFWE threshold to apply before saving out the masks. 
    %extent = extent threshold (kE). 
    %The output will be saved in a folder called 'clusters' in the same directory as the SPM.mat. 
    fparts = strsplit(spm_path, '/');
    parent_path = strjoin(fparts(1:length(fparts)-1), '/');
    cd(parent_path)
    
    % Load the SPM.mat file from the second-level analysis
    SPM = load(spm_path);
    SPM = SPM.SPM;  % Extract the SPM structure if it's nested
    
    % Check if contrasts are defined in the SPM.mat
    if isempty(SPM.xCon)
        error('No contrasts have been defined in this SPM.mat file.');
    end
    
    % Display available contrasts
    for i = 1:length(SPM.xCon)
        disp(['Contrast ' num2str(i) ': ' SPM.xCon(i).name]);
    end
    
    % Specify the contrast index (adjust this according to your analysis)
    Ic = 1;  % Example: first contrast; adjust to your needs
    
    % Set p-value and extent thresholds
    p_value = threshold;  % FWE-corrected p-value threshold (adjust if needed)
    k_extent = extent;   % Minimum cluster size in voxels
    
    % Directly set up the structure for FWE correction without triggering GUI
    xSPM.swd = pwd;                    % Directory containing SPM.mat
    xSPM.title = '';                   % Leave empty for default title
    xSPM.Ic = Ic;                      % Index of the contrast
    xSPM.thresDesc = 'FWE';            % Use FWE correction directly
    xSPM.u = p_value;                  % FWE-corrected p-value threshold
    xSPM.k = k_extent;                 % Extent threshold in voxels
    xSPM.Im = [];                      % Masking (none by default)
    xSPM.pm = [];                      % P-value adjustment (none by default)
    xSPM.Ex = 0;                       % Explicit masking (no masking)
    xSPM.units = {'mm', 'mm', 'mm'};   % Units (millimeters for voxel space)
    
    % Get the results without triggering the interactive SPM window
    [SPM, xSPM] = spm_getSPM(xSPM);
    
    % Create directory for saving clusters
    outputDir = 'clusters';
    if ~exist(outputDir, 'dir')
        mkdir(outputDir);
    end
    
    % Get cluster information using the corrected spm_clusters output
    clindex = spm_clusters(xSPM.XYZ);  % Get cluster indices for each voxel
    uniqueClusters = unique(clindex);
    
    % Loop through each cluster and save it as a NIfTI file
    V = spm_vol(xSPM.Vspm);  % Original statistical map volume
    for i = 1:length(uniqueClusters)
        % Find voxels belonging to this cluster
        voxIdx = find(clindex == uniqueClusters(i));
        if length(voxIdx) >= k_extent
            % Find the voxel with the maximum Z-score within the cluster
            [~, maxIdx] = max(xSPM.Z(voxIdx));
            peakVoxel = xSPM.XYZ(:, voxIdx(maxIdx));  % Coordinates of peak voxel
            
            % Create a new volume for this cluster
            clusterMask = zeros(V.dim);
            clusterVoxels = xSPM.XYZ(:, voxIdx);
            linearIndices = sub2ind(V.dim, clusterVoxels(1,:), clusterVoxels(2,:), clusterVoxels(3,:));
            clusterMask(linearIndices) = 1;
    
            % Create a filename using the peak coordinates
            filename = sprintf('cluster_%+d_%+d_%+d.nii', round(peakVoxel(1)), round(peakVoxel(2)), round(peakVoxel(3)));
            Vout = V;
            Vout.fname = fullfile(outputDir, filename);
            Vout.descrip = sprintf('Cluster %d, size %d voxels', i, length(voxIdx));
            spm_write_vol(Vout, clusterMask);
        end
    end
    
    disp('Cluster extraction complete!');
    
end
