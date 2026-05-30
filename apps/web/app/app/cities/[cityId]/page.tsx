import { CityDashboard } from "@/components/cities/city-dashboard";

export default async function CityDashboardPage({
  params,
}: {
  params: Promise<{ cityId: string }>;
}) {
  const { cityId } = await params;
  return <CityDashboard cityId={cityId} />;
}
