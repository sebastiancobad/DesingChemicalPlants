import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import Platform from "../components/Platform";
import Modules from "../components/Modules";
import Standards from "../components/Standards";
import Architecture from "../components/Architecture";
import Demo from "../components/Demo";
import Footer from "../components/Footer";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-[#050505] text-white">
      <Navbar />
      <main>
        <Hero />
        <Platform />
        <Modules />
        <Standards />
        <Architecture />
        <Demo />
      </main>
      <Footer />
    </div>
  );
}
