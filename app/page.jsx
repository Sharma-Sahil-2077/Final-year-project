import Image from "next/image";
import Map from "./components/Map";
import LoadingAnimation from "./components/loading"


export default function Home() {
  return (
    <main className="flex h-screen w-screen flex-col items-center">
      
      <Map />
    </main>
  );
}
