import { EmailDetailClient } from "./EmailDetailClient";

export const instant = false;

export default async function EmailDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EmailDetailClient id={id} />;
}