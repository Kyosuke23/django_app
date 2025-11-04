$(function () {
    const opt = {
        width: '100%',
        allowClear: true,
        tags: false,
        placeholder: '選択してください',
    };

    const genders = $('#id_gender');
    const employment_statuses = $('#id_employment_status');
    const privileges = $('#id_privilege');
    const groups = $('#id_groups_custom');
    genders.select2({ ...opt, placeholder: '性別を選択...' });
    employment_statuses.select2({ ...opt });
    privileges.select2({ ...opt, placeholder: '権限を選択...' });
    groups.select2({ ...opt });
});
