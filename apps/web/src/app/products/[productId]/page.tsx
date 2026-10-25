import ProductDetailClient from "./ProductDetailClient";
export const instant = false;
export default async function ProductPage({params}:{params:Promise<{productId:string}>}){
 const {productId}=await params;
 return <ProductDetailClient productId={productId}/>;
}
