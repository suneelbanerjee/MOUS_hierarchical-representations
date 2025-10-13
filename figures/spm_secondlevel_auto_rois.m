function spm_secondlevel_auto_rois(spmMatPath, varargin)
% spm_secondlevel_auto_rois
% Auto-generate ROIs from a second-level SPM at voxelwise FWE threshold,
% save masks, extract per-subject ROI means, and plot violins + scatter.
%
% Name/Value pairs:
%   'alphaFWE'      : voxelwise FWE p (default 1e-6)
%   'contrast'      : contrast index in SPM.xCon (default 1)
%   'covariateName' : substring for covariate column (optional)
%   'minVox'        : minimum cluster size in voxels (default 0)
%   'outDir'        : output directory (default 'auto_rois')
%   'firstLevelDir' : override base path for subject contrasts
%
% Example:
% spm_secondlevel_auto_rois('/path/to/SPM.mat', ...
%     'alphaFWE',1e-6, ...
%     'firstLevelDir','/media/neel/MOUS/MOUS/MOUS/SPM_results/SPM-V_Zipf_multireg');

% ---------- parse args
p = inputParser;
p.addRequired('spmMatPath', @ischar);
p.addParameter('alphaFWE', 1e-6, @(x) isnumeric(x) && x>0 && x<1);
p.addParameter('contrast', 1, @(x) isnumeric(x) && isscalar(x) && x>=1);
p.addParameter('covariateName','',@ischar);
p.addParameter('minVox', 0, @(x) isnumeric(x) && isscalar(x) && x>=0);
p.addParameter('outDir','auto_rois',@ischar);
p.addParameter('firstLevelDir','',@ischar);
p.parse(spmMatPath, varargin{:});
A = p.Results;

% ---------- load SPM
fprintf('Loading %s\n', A.spmMatPath);
load(A.spmMatPath, 'SPM');

if A.contrast > numel(SPM.xCon)
    error('Contrast index %d exceeds number of contrasts %d', A.contrast, numel(SPM.xCon));
end

% subject contrast images
Psub = cellstr(SPM.xY.P); nSub = numel(Psub);
if nSub==0, error('No subject images found in SPM.xY.P'); end

% fix subject image paths if user specifies firstLevelDir
if ~isempty(A.firstLevelDir)
    for s = 1:nSub
        [~,fname,ext] = fileparts(Psub{s});
        % Grab the subject folder name from the old path
        [subdir,~] = fileparts(Psub{s});
        [~,subfolder] = fileparts(subdir);
        % Rebuild: /firstLevelDir/sub-XXXX/con_0001.nii
        Psub{s} = fullfile(A.firstLevelDir, subfolder, [fname ext]);
    end
end

% ---------- override SPM.swd to actual folder of this SPM.mat
spmdir = fileparts(spmMatPath);
SPM.swd = spmdir;

% ---------- locate spmT file
cand = dir(fullfile(spmdir, sprintf('spmT_%04d.nii', A.contrast)));
if isempty(cand)
    cand = dir(fullfile(spmdir, sprintf('spmT_%04d.img', A.contrast)));
end
if isempty(cand)
    error('Could not find spmT_%04d.{nii,img} in %s', A.contrast, spmdir);
end
Vt = spm_vol(fullfile(spmdir, cand(1).name));

% ---------- compute T threshold
STAT = 'T'; df = SPM.xX.erdf; Tthr = NaN; used = '';
try
    xVol = SPM.xVol;
    Tthr = spm_uc(A.alphaFWE, [1 df], STAT, xVol.R, 1, xVol.S);
    used = sprintf('RFT (alpha=%.3g)', A.alphaFWE);
catch ME
    warning('RFT thresholding failed (%s). Trying u_threshold.txt ...', ME.message);
    txtfile = fullfile(spmdir,'u_threshold.txt');
    if exist(txtfile,'file')
        raw = strtrim(fileread(txtfile));
        val = str2double(raw);
        if ~isnan(val) && isfinite(val)
            Tthr = val; used = 'u_threshold.txt';
        end
    end
    if isnan(Tthr)
        Tthr = tinv(1 - A.alphaFWE, df);
        used = sprintf('uncorrected T (alpha=%.3g)', A.alphaFWE);
    end
end
fprintf('Using T-threshold = %.6f [%s]\n', Tthr, used);

% ---------- load T-map
[tImg, Vgrid] = read_vol_to_array(Vt);

% ---------- threshold + cluster
maskThr = tImg >= Tthr & isfinite(tImg);
idx = find(maskThr);
if isempty(idx), error('No voxels survive threshold %.6f.', Tthr); end
[I,J,K] = ind2sub(size(maskThr), idx);
XYZ = [I'; J'; K'];
labels = spm_clusters(XYZ);
cluIds = unique(labels);
nClusters = numel(cluIds);
sz = zeros(nClusters,1);
for c = 1:nClusters, sz(c) = sum(labels==cluIds(c)); end
keep = sz >= A.minVox;
cluIds = cluIds(keep); sz = sz(keep); nClusters = numel(cluIds);
fprintf('%d clusters remain after extent >= %d voxels.\n', nClusters, A.minVox);

if nClusters==0, error('No clusters survive.'); end

% ---------- prepare output dir
if ~exist(A.outDir,'dir'), mkdir(A.outDir); end
fid = fopen(fullfile(A.outDir,'used_T_threshold.txt'),'w');
fprintf(fid, 'Tthr=%.8f  source=%s\n', Tthr, used); fclose(fid);

% ---------- save ROI masks
roiPaths = cell(nClusters,1); roiLabels = cell(nClusters,1); peakMNI = nan(nClusters,3);
for k = 1:nClusters
    voxThis = idx(labels==cluIds(k));
    M = false(size(maskThr)); M(voxThis) = true;
    [~,peakRel] = max(tImg(voxThis));
    lin = voxThis(peakRel);
    [ix,iy,iz] = ind2sub(size(tImg), lin);
    peakXYZmm = Vgrid.mat * [ix;iy;iz;1];
    peakMNI(k,:) = peakXYZmm(1:3)';
    Vk = Vgrid; 
    Vk.fname = fullfile(A.outDir, sprintf('ROI_%02d_x%.0f_y%.0f_z%.0f_k%d.nii', ...
        k, peakMNI(k,1), peakMNI(k,2), peakMNI(k,3), sz(k)));
    spm_write_vol(Vk, double(M));
    roiPaths{k}  = Vk.fname;
    roiLabels{k} = sprintf('ROI%02d [%d vx] (%.0f,%.0f,%.0f)', ...
        k, sz(k), peakMNI(k,1), peakMNI(k,2), peakMNI(k,3));
end

% ---------- extract per-subject ROI means
Y = nan(nSub, nClusters);
for s = 1:nSub
    Vs = spm_vol(Psub{s}); Is = spm_read_vols(Vs);
    for k = 1:nClusters
        Vk = spm_vol(roiPaths{k}); Mk = spm_read_vols(Vk) > 0.5;
        if any(Vk.dim ~= Vs.dim) || max(abs(Vk.mat(:)-Vs.mat(:)))>1e-6
            Mk = reslice_mask_to_target(Vk, Vs) > 0.5;
        end
        vals = Is(Mk); Y(s,k) = mean(vals(~isnan(vals)));
    end
end

% ---------- choose x-axis covariate (or subject index)
x = (1:nSub)'; xLabel = 'Subject';
names = SPM.xX.name(:); isConst = contains(lower(names),'constant');
covCols = find(~isConst);
if ~isempty(covCols)
    chosen = covCols(1);
    if ~isempty(A.covariateName)
        hit = find(contains(lower(names), lower(A.covariateName)),1,'first');
        if ~isempty(hit) && ~isConst(hit), chosen = hit; end
    end
    x = SPM.xX.X(:,chosen); xLabel = strtrim(names{chosen});
end

% ---------- save CSV
T = array2table(Y, 'VariableNames', matlab.lang.makeValidName(roiLabels));
T.([regexprep(xLabel,'\W','_')]) = x;
csvPath = fullfile(A.outDir, 'subject_roi_means.csv');
writetable(T, csvPath);
fprintf('Wrote %s\n', csvPath);

% ---------- plots
figure('Color','w','Name','Auto ROI summary'); 
tiledlayout(1,2,'Padding','compact','TileSpacing','compact');

% (A) violin plot
nexttile(1); simple_violin(Y, 'GroupLabels', roiLabels);
ylabel('Mean contrast value'); 
title(sprintf('ROIs from spmT (Tthr=%.3f, k>=%d)', Tthr, A.minVox));

% (B) scatter for first ROI
roiToShow = 1;
nexttile(2);
scatter(x, Y(:,roiToShow), 25, 'filled'); hold on; lsline;
xlabel(xLabel); ylabel(sprintf('%s mean contrast', roiLabels{roiToShow}));
title(sprintf('Scatter: %s vs %s', xLabel, roiLabels{roiToShow})); box off;
% ---------- save figure to disk
figPathPNG = fullfile(A.outDir, 'ROI_violin_scatter.png');
figPathFIG = fullfile(A.outDir, 'ROI_violin_scatter.fig');
try
    exportgraphics(gcf, figPathPNG, 'Resolution', 300);  % better text/line quality
catch
    % fallback if exportgraphics unavailable
    saveas(gcf, figPathPNG);
end
savefig(gcf, figPathFIG);
fprintf('Saved violin+scatter to:\n  %s\n  %s\n', figPathPNG, figPathFIG);
end % main

% ---------- helpers ----------
function [img, V] = read_vol_to_array(V)
V = spm_vol(V); img = spm_read_vols(V);
end

function Mres = reslice_mask_to_target(Vmask, Vtgt)
[xt,yt,zt] = ndgrid(1:Vtgt.dim(1),1:Vtgt.dim(2),1:Vtgt.dim(3));
M = inv(Vmask.mat) * Vtgt.mat;
xyz = M * [xt(:)'; yt(:)'; zt(:)'; ones(1,numel(xt))];
vals = spm_sample_vol(Vmask, xyz(1,:), xyz(2,:), xyz(3,:), 0);
Mres = reshape(vals, Vtgt.dim) > 0.5;



end

function simple_violin(Y, varargin)
% Just draws the violins; does NOT save anything.
p = inputParser;
p.addParameter('GroupLabels', {}, @(x) iscellstr(x) || isstring(x));
p.parse(varargin{:});
lab = p.Results.GroupLabels;

[nSub, nROI] = size(Y);
hold on;
for r = 1:nROI
    yi = Y(:,r); yi = yi(~isnan(yi));
    if numel(yi) < 3, continue; end
    [f,xi] = ksdensity(yi, 'Function','pdf');
    f = f / max(f) * 0.35;
    xv = [r - f, fliplr(r + f)];
    yv = [xi, fliplr(xi)];
    patch(xv, yv, 0.85*[1 1 1], 'EdgeColor',[0.5 0.5 0.5]);
    med = median(yi); q = quantile(yi,[0.25 0.75]);
    plot([r-0.25 r+0.25],[med med],'k-','LineWidth',1.5);
    plot([r r], q, 'k-','LineWidth',1.0);
    jitter = (rand(size(yi))-0.5)*0.15;
    scatter(r + jitter, yi, 12, 'filled', 'MarkerFaceAlpha',0.6);
end
xlim([0.5 nROI+0.5]); set(gca,'XTick',1:nROI,'XTickLabel',lab,'XTickLabelRotation',15);
box off;
end
