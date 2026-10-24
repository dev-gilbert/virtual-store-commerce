import type { Metadata } from "next";
import AdminDashboard from "@/components/admin/AdminDashboard";
export const metadata:Metadata={title:"Retailer Control Room | Virtual Store Commerce"};
export default function AdminPage(){return <AdminDashboard/>}