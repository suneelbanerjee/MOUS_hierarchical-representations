%% Calculate ROI center of gravity

%0. Install CosmoMVPA (cosmomvpa.org)
%1. Use SPM12 to export individual clusters as binary nifti masks from the thresholded group-level results. 
%2. This script then takes in the cluster masks, masks the T-map with each,
%and returns the center of mass within each mask in the right column of
%'table'
%
function table = cluster_center_of_mass(roi_dir,nifti)
    addpath(genpath('/home/neelbanerjee/SPM12'))
    addpath(genpath('/Users/neel/Documents/MATLAB/CoSMoMVPA-master/mvpa'))
    %Set path to cluster mask ROIs. 
    if nargin < 1
        roi_dir = 'clusters';
    end
    cd(roi_dir)
    roi_dir= dir('*.nii');
    rois = extractfield(roi_dir,'name');
    table = string(rois);
    %Path to T-map
    % cd ../
    % nifti = 'spmT_0001.nii';

    for n = 1:length(rois)
        mask = char(rois(n));
        ds = cosmo_fmri_dataset(nifti, 'mask',mask);
        sumT = sum(ds.samples);
        coords = cosmo_vol_coordinates(ds);
        x = sum(coords(1,:) .* ds.samples)/sumT;
        y = sum(coords(2,:) .* ds.samples)/sumT;
        z = sum(coords(3,:) .* ds.samples)/sumT;
        table(2,n) = strcat(num2str(x),",",num2str(y),",",num2str(z));
    end
    table = transpose(table);
    T = array2table(table, 'VariableNames', {'ROI', 'Coordinates'});
    writetable(T, 'SPM_results_center_of_mass.csv');

end