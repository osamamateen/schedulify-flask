// Call the dataTables jQuery plugin
$(document).ready(function () {
  $('#dataTable').DataTable({
    dom: 'Bfrtip',
    buttons: ['copy', 'csv', 'excel', 'pdf', 'print'],
  })
  $('#dataTable2').DataTable({
    dom: 'Bfrtip',
  })
})
