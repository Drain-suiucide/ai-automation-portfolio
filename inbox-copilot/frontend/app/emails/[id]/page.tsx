export const instant = false;

export default async function EmailDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <div>Email detail: {id} (coming in 8.2)</div>;
}