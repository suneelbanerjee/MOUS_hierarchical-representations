function results_and_height(spm_dot_mat,pFWE)
    spm('defaults', 'FMRI');
    export_spm_results_to_csv(spm_dot_mat, pFWE)
    spm_height_threshold = xSPM.u;
    writelines(strcat("u = ",num2str(spm_height_threshold)),'u_threshold.txt')
end
