function [outZ, stats, outZthr, outZclust] = spmT_to_Z( ...
    tFile, spmMat, outFile, maskFile, varargin)
% Convert an SPM T-map to a Z-map, optionally apply an uncorrected p-threshold,
% and an optional cluster-extent threshold (voxels or mm^3).
%
% REQUIRED
%   tFile    : path to spmT_*.nii
%   spmMat   : path to SPM.mat (to read residual df)
%   outFile  : output Z-map filename (unthresholded Z)
%
% OPTIONAL
%   maskFile : ([]) path to binary/weighted mask; voxels with mask<=0 or NaN are set to 0
%
% NAME–VALUE PAIRS (all optional)
%   'p'           : [] (no voxelwise threshold) or scalar uncorrected p (e.g., 1e-6)
%   'tail'        : 'two' (default) | 'one'
%   'direction'   : 'both' (default), 'pos', or 'neg'
%                   (If tail='one', use 'pos' for positive or 'neg' for negative.)
%   'subval'      : 0 (value for subthreshold voxels; NaN is also useful for viewers)
%   'thrFile'     : '' (filename for voxelwise-thresholded Z; default adds suffix)
%   'k'           : [] (cluster-extent threshold in voxels; applied after voxelwise threshold)
%   'kmm3'        : [] (cluster-extent threshold in mm^3; overrides 'k' if provided)
%   'connectivity': 26 (3D connectivity: 6 | 18 | 26)
%   'separateSigns': true (cluster positive and negative separately when applicable)
%
% RETURNS
%   outZ      : path to unthresholded Z image
%   stats     : struct with fields df, p, tail, direction, zcrit, k_vox, k_mm3, connectivity
%   outZthr   : path to voxelwise-thresholded Z (empty if 'p' not provided)
%   outZclust : path to cluster-extent–thresholded Z (empty if no cluster threshold requested)
%
% EXAMPLES
%   % Two-sided p<1e-6, cluster extent >= 20 voxels, 26-connectivity (default)
%   spmT_to_Z('spmT_0001.nii','SPM.mat','spmZ_0001.nii',[], ...
%             'p',1e-6,'tail','two','k',20);
%
%   % One-sided (positive) p<1e-3, extent >= 200 mm^3, 18-connectivity, NaN out
%   spmT_to_Z('spmT_0002.nii','SPM.mat','spmZ_0002.nii',[], ...
%             'p',1e-3,'tail','one','direction','pos','kmm3',200,'connectivity',18,'subval',NaN);

    % ------------ Parse inputs ------------
    if ~exist('maskFile','var'); maskFile = []; end
    p = inputParser;
    addParameter(p,'p',[],@(x) isempty(x) || (isscalar(x) && x>0 && x<1));
    addParameter(p,'tail','two',@(s) any(strcmpi(s,{'one','two'})));
    addParameter(p,'direction','both',@(s) any(strcmpi(s,{'both','pos','neg'})));
    addParameter(p,'subval',0,@(x) isscalar(x) && (isnumeric(x) || islogical(x)));
    addParameter(p,'thrFile','',@(s) ischar(s) || isstring(s));
    addParameter(p,'k',[],@(x) isempty(x) || (isscalar(x) && x>=0));
    addParameter(p,'kmm3',[],@(x) isempty(x) || (isscalar(x) && x>=0));
    addParameter(p,'connectivity',26,@(x) ismember(x,[6 18 26]));
    addParameter(p,'separateSigns',true,@(x) islogical(x) && isscalar(x));
    parse(p,varargin{:});
    opts = p.Results;

    % ------------ Degrees of freedom ------------
    S  = load(spmMat, 'SPM');
    df = S.SPM.xX.erdf;

    % ------------ Read T image ------------
    Vt    = spm_vol(tFile);
    [T,~] = spm_read_vols(Vt);

    % ------------ Robust T -> Z (one-sided mapping preserving sign) ------------
    P  = tcdf(T, df);
    P  = min(max(P, realmin), 1 - eps);  % clamp to (0,1)
    Z  = norminv(P);

    % ------------ Optional masking ------------
    if ~isempty(maskFile)
        Vm = spm_vol(maskFile);
        M  = spm_read_vols(Vm);
        Z(M<=0 | isnan(M)) = 0;
    end

    % ------------ Write unthresholded Z ------------
    Vz         = Vt;
    Vz.fname   = outFile;
    Vz.descrip = sprintf('Z from %s (df=%g)', Vt.fname, df);
    spm_write_vol(Vz, Z);
    outZ = outFile;

    % ------------ Prepare stats struct ------------
    stats = struct('df',df,'p',opts.p,'tail',lower(opts.tail), ...
                   'direction',lower(opts.direction),'zcrit',[], ...
                   'k_vox',[],'k_mm3',[],'connectivity',opts.connectivity);

    % ------------ Early exit if no p-threshold and no cluster threshold ------------
    outZthr   = '';
    outZclust = '';
    if isempty(opts.p) && isempty(opts.k) && isempty(opts.kmm3)
        return;
    end

    % ------------ Compute Z-critical and voxelwise mask(s) ------------
    if ~isempty(opts.p)
        switch lower(opts.tail)
            case 'two'
                zcrit = -norminv(opts.p/2);       % |Z| >= zcrit
            case 'one'
                zcrit = -norminv(opts.p);         % Z >= zcrit (pos) or Z <= -zcrit (neg)
        end
        stats.zcrit = zcrit;
    else
        % If no p provided, treat every nonzero (or non-NaN) voxel as candidate
        zcrit = -Inf;
        stats.zcrit = zcrit;
    end

    % Build sign-aware suprathreshold logical masks from Z (do not rely on subval)
    mask_pos = Z >= max(zcrit, 0);         % positive side
    mask_neg = Z <= -max(zcrit, 0);        % negative side
    mask_any = false(size(Z));
    switch lower(opts.tail)
        case 'two'
            if opts.separateSigns
                % keep separate masks; combine only for writing voxelwise threshold
                mask_any = mask_pos | mask_neg;
            else
                % cluster on absolute value (both signs together)
                mask_any = (abs(Z) >= zcrit);
            end
        case 'one'
            if strcmpi(opts.direction,'pos')
                mask_any = mask_pos;
            elseif strcmpi(opts.direction,'neg')
                mask_any = mask_neg;
            else
                error('For tail="one", set direction="pos" or "neg".');
            end
    end

    % ------------ Write voxelwise-thresholded Z ------------
    Zthr = apply_subval(Z, mask_any, opts.subval);
    if isempty(opts.thrFile)
        outZthr = add_suffix_to_filename(outFile, sprintf('_thr_p%s', p_to_str(opts.p)));
    else
        outZthr = opts.thrFile;
    end
    Vzt         = Vz;
    Vzt.fname   = outZthr;
    Vzt.descrip = sprintf('Z voxelwise-thresholded: p_unc=%s, tail=%s, dir=%s, zcrit=%.3f', ...
                          num2str_or_na(opts.p), opts.tail, opts.direction, stats.zcrit);
    spm_write_vol(Vzt, Zthr);

    % ------------ Cluster-extent thresholding (optional) ------------
    if isempty(opts.k) && isempty(opts.kmm3)
        return; % no cluster filter requested
    end

    % Connectivity kernel
    conn = connectivity_kernel(opts.connectivity);

    % Convert mm^3 threshold to voxels if needed
    voxvol = abs(det(Vt.mat(1:3,1:3)));   % mm^3 per voxel
    if ~isempty(opts.kmm3)
        Kvox = max(1, round(opts.kmm3 / voxvol));
        stats.k_mm3 = opts.kmm3;
        stats.k_vox = Kvox;
    else
        Kvox = round(opts.k);
        stats.k_vox = Kvox;
        stats.k_mm3 = Kvox * voxvol;
    end

    Zcl = Zthr; % start from voxelwise-thresholded map

    if strcmpi(opts.tail,'two') && opts.separateSigns
        % Cluster positive and negative separately
        Zcl(~mask_pos) = apply_subval(Zcl(~mask_pos), false(size(Zcl(~mask_pos))), opts.subval); % no-op
        Zcl(~mask_neg) = apply_subval(Zcl(~mask_neg), false(size(Zcl(~mask_neg))), opts.subval); % no-op

        % Positive clusters
        Zcl = keep_large_components(Zcl, mask_pos, Kvox, conn, opts.subval);
        % Negative clusters
        Zcl = keep_large_components(Zcl, mask_neg, Kvox, conn, opts.subval);

    else
        % Cluster on combined mask (either one-sided or two-sided not separating signs)
        Zcl = keep_large_components(Zcl, mask_any, Kvox, conn, opts.subval);
    end

    % Write cluster-thresholded map
    outZclust      = add_suffix_to_filename(outZthr, sprintf('_k%dvox', Kvox));
    Vzc            = Vz;
    Vzc.fname      = outZclust;
    Vzc.descrip    = sprintf('Z voxelwise+cluster-thresholded: k=%d vox (%.1f mm^3), conn=%d', ...
                              Kvox, stats.k_mm3, opts.connectivity);
    spm_write_vol(Vzc, Zcl);
end

% -------- Helper: apply subval outside mask --------
function Zout = apply_subval(Zin, mask_keep, subval)
    Zout = Zin;
    Zout(~mask_keep) = subval;
end

% -------- Helper: keep only components >= Kvox --------
function Zout = keep_large_components(Zin, mask, Kvox, conn, subval)
    Zout = Zin;
    if ~any(mask(:)); return; end
    CC = bwconncomp(mask, conn);
    % Find components that meet size
    keep = false(size(mask));
    for i = 1:CC.NumObjects
        vox_idx = CC.PixelIdxList{i};
        if numel(vox_idx) >= Kvox
            keep(vox_idx) = true;
        end
    end
    % Subval out small clusters
    Zout(mask & ~keep) = subval;
end

% -------- Helper: connectivity kernel (6 / 18 / 26) --------
function conn = connectivity_kernel(n)
    switch n
        case 6
            conn = conndef(3,'minimal');   % faces only
        case 26
            conn = conndef(3,'maximal');   % faces + edges + corners
        case 18
            % faces + edges (exclude corners)
            conn = ones(3,3,3);
            % zero out the 8 corners
            corners = [ 1 1 1; 1 1 3; 1 3 1; 1 3 3; 3 1 1; 3 1 3; 3 3 1; 3 3 3 ];
            for i=1:size(corners,1), conn(corners(i,1),corners(i,2),corners(i,3)) = 0; end
        otherwise
            error('connectivity must be 6, 18, or 26');
    end
end

% -------- Helper: p string for filenames --------
function s = p_to_str(p)
    if isempty(p), s = 'NA'; return; end
    if p < 1e-3
        s = sprintf('%0.0e', p);
    else
        s = strrep(sprintf('%0.3f', p),'.','p'); % e.g., 0p010
    end
end

% -------- Helper: add suffix before extension (handles .nii / .nii.gz) --------
function out = add_suffix_to_filename(fname, suffix)
    [pth,nam,ext] = fileparts(fname);
    if strcmpi(ext,'.gz')
        [pth2,nam2,ext2] = fileparts(nam); % ext2 should be .nii
        out = fullfile(pth, [nam2, suffix, ext2, '.gz']);
    else
        out = fullfile(pth, [nam, suffix, ext]);
    end
end

% -------- Helper: num2str or 'NA' --------
function s = num2str_or_na(x)
    if isempty(x), s = 'NA'; else, s = num2str(x); end
end



% % cd(Second level SPM directory)
% [outZ, stats, outZthr, outZclust] = spmT_to_Z( ...
%     'spmT_0001.nii', 'SPM.mat', 'spmZ_0001.nii', [], ...
%     'p', 1e-12, 'tail','one', 'direction','pos', 'k', 20);