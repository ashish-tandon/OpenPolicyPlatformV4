import { Link } from "react-router-dom";
import { FaFacebookF, FaTwitter, FaInstagram } from "react-icons/fa";

const Footer = () => {
  return (
    <footer className="bg-[#111111] text-white mt-20">
      <div className="padding-x max-container py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <h2 className="text-[32px] font-['SFProDisplay'] leading-[40px] mb-4">
              We develop and create
              <br />
              digital future
            </h2>
          </div>
          <div>
            <h3 className="text-[16px] font-['SFProTextMedium'] mb-4">
              Address
            </h3>
            <p className="text-[14px] mb-2">The USA -</p>
            <p className="text-[14px]">390 Queens Quay W Unit 406</p>
            <p className="text-[14px]">Toronto, ON M5A 0H4</p>
            <p className="text-[14px]">Canada</p>
          </div>
          <div>
            <h3 className="text-[16px] font-['SFProTextMedium'] mb-4">
              Say Hello
            </h3>
            <p className="text-[14px] mb-2">info@openpolicy.me</p>
            <p className="text-[14px]">+1 (613) 608-5472</p>
          </div>
        </div>
        <div className="flex gap-4 mt-8">
          <Link
            to="#"
            className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <FaFacebookF size={16} />
          </Link>
          <Link
            to="#"
            className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <FaTwitter size={16} />
          </Link>
          <Link
            to="#"
            className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center hover:bg-white/10 transition-colors"
          >
            <FaInstagram size={16} />
          </Link>
        </div>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mt-16 pt-8 border-t border-white/10">
          <div className="flex gap-8 mb-4 md:mb-0">
            <Link to="#" className="text-[14px] hover:text-white/80">
              About Us
            </Link>
            <Link to="#" className="text-[14px] hover:text-white/80">
              Contact
            </Link>
          </div>
          <p className="text-[14px] text-white/80">Alrights Reserved © 2025</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
