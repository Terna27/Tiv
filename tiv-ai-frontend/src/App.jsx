import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import About from "./pages/About";
import Contribute from "./pages/Contribute";
import ContributeText from "./pages/ContributeText";
import ContributeTranslation from "./pages/ContributeTranslation";
import ContributeVoice from "./pages/ContributeVoice";
import Review from "./pages/Review";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/contribute" element={<Contribute />} />
        <Route path="/contribute/text" element={<ContributeText />} />
        <Route path="/contribute/translation" element={<ContributeTranslation />} />
        <Route path="/contribute/voice" element={<ContributeVoice />} />
        <Route path="/review" element={<Review />} />
      </Routes>
    </Layout>
  );
}
