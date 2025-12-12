function spm_secondlevel_auto_rois(spmMatPath, varargin)
% spm_secondlevel_auto_rois
% Build FWE-thresholded cluster ROIs from a second-level SPM, save masks,
% extract per-subject ROI means, and plot violins + a scatter.
%
% Inputs (name/value):
%   'alphaFWE'      : voxelwise FWE p (default 0.05)
%   'contrast'      : contrast index in SPM.xCon (default 1)
%   'covariateName' : (optional) substring to choose SPM.xX column for scatter x
%   'minVox'        : minimum cluster size in voxels (default 0)
%   'outDir'        : output directory for masks/CSV (default 'auto_rois')
%
% Requires SPM12 on path.

% ---------- parse
p = inputParser;
p.addRequired('spmMatPath', @ischar);
p.addParameter('alphaFWE', 0.05, @(x) isnumeric(x) && x>0 && x<1);
p.addParameter('contrast', 1, @(x) isnumeric(x) && isscalar(x) && x>=1);
p.addParameter('covariateName','',@ischar);
p.addParameter('minVox', 0, @(x) isnumeric(x) && isscalar(x) && x>=0);
p.addParameter('outDir','auto_rois',@ischar);
p.parse(spmMatPath, varargin{:});
A = p.Results;

% ---------- load SPM, get subject images and T-map
fprintf('Loading %s\n', A.spmMatPath);
load(A.spmMatPath, 'SPM');
if A.contrast > numel(SPM.xCon)
    error('contrast index %d exceeds SPM.xCon length %d', A.contrast, numel(SPM.xCon));
end
Psub = cellstr(SPM.xY.P);
nSub = numel(Psub);
if nSub==0, error('No subject images found in SPM.xY.P'); end

% Try to find spmT for this contrast
Vt = [];
if isfield(SPM.xCon(A.contrast),'Vspm') && ~isempty(SPM.xCon(A.contrast).Vspm)
    Vt = SPM.xCon(A.contrast).Vspm;
else
    % fall back: look for spmT_####.nii in same dir
    spmdir = SPM.swd;
    cand = dir(fullfile(spmdir, sprintf('spmT_%04d.nii', A.contrast)));
    if isempty(cand)
        % also try img
        cand = dir(fullfile(spmdir, sprintf('spmT_%04d.img', A.contrast)));
    end
    if isempty(cand)
        error('Could not find spmT for contrast %d in %s', A.contrast, spmdir);
    end
    Vt = spm_vol(fullfile(spmdir, cand(1).name));
end

% ---------- compute voxelwise FWE T threshold
STAT = 'T';
try
    df = SPM.xX.erdf;      % residual df (scalar at second level)
catch
    error('SPM.xX.erdf not found; was the model estimated?');
end

Tthr = [];
try
    % SPM random-field theory-based u (height) for voxelwise FWE
    % spm_uc(alpha, df, STAT, R, n, S) needs xVol fields
    xVol = SPM.xVol;
    Tthr = spm_uc(A.alphaFWE, [1 df], STAT, xVol.R, 1, xVol.S);
    fprintf('FWE voxelwise T-threshold = %.4f (alpha = %.3g)\n', Tthr, A.alphaFWE);
catch ME
    warning('RFT thresholding failed (%s). Falling back to uncorrected: tinv(1-alpha,df).', ME.message);
    Tthr = tinv(1 - A.alphaFWE, df);
    fprintf('Uncorrected T-threshold (alpha=%.3g) = %.4f\n', A.alphaFWE, Tthr);
end

% ---------- load T-map and threshold
[tImg, XYZmm, Vgrid] = read_vol_to_array(Vt);
maskThr = tImg >= Tthr & isfinite(tImg);

% remove NaNs & apply min cluster extent
CC = bwconncomp(maskThr, 6);
nClusters = CC.NumObjects;
fprintf('Found %d clusters above threshold.\n', nClusters);

% filter by extent
keep = true(1,nClusters);
sz = cellfun(@numel, CC.PixelIdxList);
if A.minVox > 0
    keep = sz >= A.minVox;
end
CC.PixelIdxList = CC.PixelIdxList(keep);
sz = sz(keep);
nClusters = numel(CC.PixelIdxList);
fprintf('%d clusters remain after extent >= %d voxels.\n', nClusters, A.minVox);

if nClusters==0
    error('No clusters survive. Try a more lenient threshold or smaller minVox.');
end

% ---------- prepare output dir
if ~exist(A.outDir,'dir'), mkdir(A.outDir); end

% ---------- save each cluster as NIfTI, collect peaks & labels
roiPaths = cell(nClusters,1);
roiLabels = cell(nClusters,1);
peakMNI   = nan(nClusters,3);

for k = 1:nClusters
    M = false(size(maskThr)); 
    M(CC.PixelIdxList{k}) = true;

    % peak voxel within cluster
    [~,peakIdx] = max(tImg(CC.PixelIdxList{k}));
    lin = CC.PixelIdxList{k}(peakIdx);
    [ix,iy,iz] = ind2sub(size(tImg), lin);
    peakXYZ = Vgrid.mat * [ix;iy;iz;1];
    peakMNI(k,:) = peakXYZ(1:3)';
    
    % write mask
    Vk = Vgrid; 
    Vk.fname = fullfile(A.outDir, sprintf('ROI_%02d_x%.0f_y%.0f_z%.0f_k%d.nii', ...
        k, peakMNI(k,1), peakMNI(k,2), peakMNI(k,3), sz(k)));
    spm_write_vol(Vk, double(M));
    roiPaths{k}  = Vk.fname;
    roiLabels{k} = sprintf('ROI%02d [%d vx] (%.0f,%.0f,%.0f)', k, sz(k), peakMNI(k,1), peakMNI(k,2), peakMNI(k,3));
end

% ---------- extract per-subject ROI means
Y = nan(nSub, nClusters);
for s = 1:nSub
    Vs = spm_vol(Psub{s});
    Is = spm_read_vols(Vs);
    for k = 1:nClusters
        Vk = spm_vol(roiPaths{k});
        Mk = spm_read_vols(Vk) > 0.5;
        % assume same grid; if not, resample mask
        if any(Vk.dim ~= Vs.dim) || max(abs(Vk.mat(:)-Vs.mat(:)))>1e-6
            Mk = reslice_mask_to_target(Vk, Vs) > 0.5;
        end
        vals = Is(Mk);
        Y(s,k) = mean(vals(~isnan(vals)));
    end
end

% ---------- choose x-axis covariate (or subject index)
x = (1:nSub)'; xLabel = 'Subject';
names = SPM.xX.name(:);
isConst = contains(lower(names),'constant');
covCols = find(~isConst);
if ~isempty(covCols)
    chosen = covCols(1);
    if ~isempty(A.covariateName)
        hit = find(contains(lower(names), lower(A.covariateName)),1,'first');
        if ~isempty(hit) && ~isConst(hit), chosen = hit; end
    end
    x = SPM.xX.X(:,chosen);
    xLabel = strtrim(names{chosen});
end

% ---------- save CSV of subject×ROI means
T = array2table(Y, 'VariableNames', matlab.lang.makeValidName(roiLabels));
T.([regexprep(xLabel,'\W','_')]) = x;
csvPath = fullfile(A.outDir, 'subject_roi_means.csv');
writetable(T, csvPath);
fprintf('Wrote %s\n', csvPath);

% ---------- plots
figure('Color','w','Name','Auto ROI summary'); 
tiledlayout(1,2,'Padding','compact','TileSpacing','compact');

% (A) violin plot
nexttile(1);
simple_violin(Y, 'GroupLabels', roiLabels);
ylabel('Mean contrast value'); 
title(sprintf('ROIs from spmT (alpha_{FWE}=%.3g, k>=%d)', A.alphaFWE, A.minVox));

% (B) scatter for first ROI
roiToShow = 1;
nexttile(2);
scatter(x, Y(:,roiToShow), 25, 'filled'); hold on; lsline;
xlabel(xLabel); ylabel(sprintf('%s mean contrast', roiLabels{roiToShow}));
title(sprintf('Scatter: %s vs %s', xLabel, roiLabels{roiToShow})); box off;

% also print a quick summary table to console
disp(head(T, min(10,height(T))));

end % main

% ---------- helpers ----------
function [img, XYZmm, V] = read_vol_to_array(V)
V = spm_vol(V);
img = spm_read_vols(V);
[x,y,z] = ndgrid(1:V.dim(1),1:V.dim(2),1:V.dim(3));
XYZmm = V.mat * [x(:)'; y(:)'; z(:)'; ones(1,numel(x))];
end

function Mres = reslice_mask_to_target(Vmask, Vtgt)
% nearest-neighbor resampling of binary mask to target grid
[xt,yt,zt] = ndgrid(1:Vtgt.dim(1),1:Vtgt.dim(2),1:Vtgt.dim(3));
M = inv(Vmask.mat) * Vtgt.mat;
xyz = M * [xt(:)'; yt(:)'; zt(:)'; ones(1,numel(xt))];
vals = spm_sample_vol(Vmask, xyz(1,:), xyz(2,:), xyz(3,:), 0);
Mres = reshape(vals, Vtgt.dim) > 0.5;
end

function simple_violin(Y, varargin)
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
    med = median(yi);
    q = quantile(yi,[0.25 0.75]);
    plot([r-0.25 r+0.25],[med med],'k-','LineWidth',1.5);
    plot([r r], q, 'k-','LineWidth',1.0);
    jitter = (rand(size(yi))-0.5)*0.15;
    scatter(r + jitter, yi, 12, 'filled', 'MarkerFaceAlpha',0.6);
end
xlim([0.5 nROI+0.5]);
set(gca,'XTick',1:nROI,'XTickLabel',lab,'XTickLabelRotation',15);
box off;
end