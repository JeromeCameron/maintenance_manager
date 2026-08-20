import type { CustomReportRequest, CustomReportResponse, ReportBuilderMetadata } from "~/types"

export function useReportBuilder() {
  const { get, post } = useApi()

  const getMetadata = () => get<ReportBuilderMetadata>("/reports/custom/metadata")
  const runReport = (req: CustomReportRequest) => post<CustomReportResponse>("/reports/custom", req)

  return { getMetadata, runReport }
}
