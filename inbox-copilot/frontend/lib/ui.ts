export function priorityColor(priority: string | null): string {
  switch (priority) {
    case "P0": return "bg-red-100 text-red-800 border-red-300";
    case "P1": return "bg-orange-100 text-orange-800 border-orange-300";
    case "P2": return "bg-yellow-100 text-yellow-800 border-yellow-300";
    case "P3": return "bg-gray-100 text-gray-700 border-gray-300";
    default: return "bg-gray-50 text-gray-500 border-gray-200";
  }
}

export function categoryColor(category: string | null): string {
  switch (category) {
    case "billing": return "bg-blue-100 text-blue-800";
    case "support": return "bg-purple-100 text-purple-800";
    case "sales": return "bg-green-100 text-green-800";
    case "spam": return "bg-red-100 text-red-800";
    case "partnership": return "bg-teal-100 text-teal-800";
    default: return "bg-gray-100 text-gray-700";
  }
}

export function draftStatusColor(status: string): string {
  switch (status) {
    case "approved": return "bg-green-100 text-green-800";
    case "rejected": return "bg-red-100 text-red-800";
    case "sent": return "bg-blue-100 text-blue-800";
    case "draft": return "bg-yellow-100 text-yellow-800";
    default: return "bg-gray-100 text-gray-700";
  }
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}