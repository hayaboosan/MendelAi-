jQuery(function ($) {
    // デフォルトの設定を変更
    $.extend($.fn.dataTable.defaults, {
        language: {
            url: 'http://cdn.datatables.net/plug-ins/9dcbecd42ad/i18n/Japanese.json',
        },
    });

    // $(document).ready(function () {
    //     $('#datatable').DataTable({
    //         scrollX: true,
    //         stateSave: true,
    //     });
    // });
    $(document).ready(function () {
        // Setup - add a text input to each footer cell
        $('#datatable tfoot th').each(function () {
            var title = $(this).text();
            $(this).html(
                '<input type="text" placeholder="Search ' + title + '" />'
            );
        });

        // DataTable
        var table = $('#datatable').DataTable({
            // リロード時の検索条件保存
            stateSave: false,

            // 水平スクロール
            scrollX: true,

            // 垂直スクロール
            scrollY: '50vh',
            scrollCollapse: true,
            paging: false,

            initComplete: function () {
                // フッターの列検索
                this.api()
                    .columns()
                    .every(function () {
                        var that = this;
                        $('input', this.footer()).on(
                            'keyup change clear',
                            function () {
                                if (that.search() !== this.value) {
                                    that.search(this.value).draw();
                                }
                            }
                        );
                    });
            },
            // 下に足すならここから
        });
    });
});
