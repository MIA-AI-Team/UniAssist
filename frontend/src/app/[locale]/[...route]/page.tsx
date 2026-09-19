import { FeatureRoute } from "@/features/route";
export default async function Page({
  params,
}: {
  params: Promise<{ route: string[] }>;
}) {
  const { route } = await params;
  return <FeatureRoute route={route} />;
}
