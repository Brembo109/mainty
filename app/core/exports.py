import csv
from collections.abc import Iterable
from datetime import date, datetime
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openpyxl import Workbook


EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_XLSX = "xlsx"
EXPORT_FORMATS = {EXPORT_FORMAT_CSV, EXPORT_FORMAT_XLSX}


def build_export_filename(prefix: str, export_format: str) -> str:
    timestamp = timezone.localtime().strftime("%Y-%m-%d_%H%M")
    return f"{prefix}_{timestamp}.{export_format}"


def export_queryset_response(*, rows: Iterable[list[str]], headers: list[str], filename: str, export_format: str) -> HttpResponse:
    if export_format == EXPORT_FORMAT_CSV:
        return build_csv_response(rows=rows, headers=headers, filename=filename)
    if export_format == EXPORT_FORMAT_XLSX:
        return build_xlsx_response(rows=rows, headers=headers, filename=filename)
    raise ValueError(f"Unsupported export format: {export_format}")


def build_csv_response(*, rows: Iterable[list[str]], headers: list[str], filename: str) -> HttpResponse:
    buffer = StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(headers)
    writer.writerows(rows)

    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def build_xlsx_response(*, rows: Iterable[list[str]], headers: list[str], filename: str) -> HttpResponse:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Export"
    worksheet.append(headers)

    for row in rows:
        worksheet.append(row)

    autosize_worksheet_columns(worksheet)

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    workbook.save(response)
    return response


def autosize_worksheet_columns(worksheet) -> None:
    for column_cells in worksheet.columns:
        values = [len(str(cell.value or "")) for cell in column_cells]
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(values + [10]) + 2, 50)


def stringify_export_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(_("Ja")) if value else str(_("Nein"))
    if isinstance(value, datetime):
        localized = timezone.localtime(value) if timezone.is_aware(value) else value
        return localized.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


class ListExportMixin:
    export_filename_prefix = "export"
    export_headers: list[str] = []

    def get_export_queryset(self):
        return self.get_queryset()

    def get_export_rows(self, queryset) -> list[list[str]]:
        raise NotImplementedError

    def get_export_headers(self) -> list[str]:
        return self.export_headers

    def get_export_filename_prefix(self) -> str:
        return self.export_filename_prefix

    def get_export_filename(self, export_format: str) -> str:
        return build_export_filename(self.get_export_filename_prefix(), export_format)

    def get_export_urls(self) -> dict[str, str]:
        current_params = self.request.GET.copy()
        current_params.pop("page", None)
        urls = {}
        for export_format in sorted(EXPORT_FORMATS):
            params = current_params.copy()
            params["export"] = export_format
            urls[export_format] = f"?{params.urlencode()}"
        return urls

    def maybe_export(self):
        export_format = self.request.GET.get("export", "").strip().lower()
        if export_format not in EXPORT_FORMATS:
            return None

        queryset = self.get_export_queryset()
        rows = self.get_export_rows(queryset)
        return export_queryset_response(
            rows=rows,
            headers=self.get_export_headers(),
            filename=self.get_export_filename(export_format),
            export_format=export_format,
        )

    def render_to_response(self, context, **response_kwargs):
        export_response = self.maybe_export()
        if export_response is not None:
            return export_response
        return super().render_to_response(context, **response_kwargs)
