import React from 'react';
import Image from "next/image";
import Link from "next/link";
import Modal from './Settings/Modal';
import { ChatBoxSettings } from '@/types/data';

interface FooterProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
}

const Footer: React.FC<FooterProps> = ({ chatBoxSettings, setChatBoxSettings }) => {
  // Add domain filtering from URL parameters
  if (typeof window !== 'undefined') {
    const urlParams = new URLSearchParams(window.location.search);
    const urlDomains = urlParams.get("domains");
    if (urlDomains) {
      // Split domains by comma if multiple domains are provided
      const domainArray = urlDomains.split(',').map(domain => ({
        value: domain.trim()
      }));
      localStorage.setItem('domainFilters', JSON.stringify(domainArray));
    }
  }

  return (
    <>
      <div className="container flex flex-col sm:flex-row min-h-[60px] sm:min-h-[72px] mt-2 items-center justify-center border-t border-gray-700/30 px-4 pb-3 pt-4 sm:py-5 lg:px-0 bg-transparent backdrop-blur-sm gap-3 sm:gap-0">
        <Modal setChatBoxSettings={setChatBoxSettings} chatBoxSettings={chatBoxSettings} />
        <div className="text-xs sm:text-sm text-gray-100 text-center order-1">
            © {new Date().getFullYear()} GPT Researcher. All rights reserved.
        </div>
      </div>
    </>
  );
};

export default Footer;