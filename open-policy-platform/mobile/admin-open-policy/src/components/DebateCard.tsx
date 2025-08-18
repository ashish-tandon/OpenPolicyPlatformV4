import React, { useState, useRef, useEffect } from 'react';
import parse, { domToReact } from 'html-react-parser';
import { Link, useLocation } from 'react-router-dom';

export interface Debate {
  name: string;
  riding: string;
  party: string;
  statement: string;
  topic: string;
  sub_topics: string;
  datetime: string;
  profile_url: string;
  image: string;
}

interface DebateCardProps {
  debate: Debate;
  index: number;
  politician: null | string;
  number: null | string;
}

const options = {
  replace: (domNode: import('html-react-parser').DOMNode) => {
    if (domNode.type === 'tag' && domNode.name === 'a') {
      const { href } = domNode.attribs || {};
      if (href && href.startsWith('/')) {
        return (
          <Link
            to={href}
            className="text-[#628ECB] hover:text-[#4A6B99] transition-colors"
          >
            {domToReact(
              domNode.children as import('html-react-parser').DOMNode[],
              options,
            )}
          </Link>
        );
      }
    }
  },
};

// Global scroll state
let hasScrolled = false;
let lastPath = '';

const DebateCard: React.FC<any> = ({ debate, index, politician = null }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const location = useLocation(); // Used to detect route changes

  useEffect(() => {
    // Reset scroll state if path changed (e.g., user navigated back)
    if (lastPath !== location.pathname) {
      hasScrolled = false;
      lastPath = location.pathname;
    }

    // Scroll to the first matching politician's card
    if (!hasScrolled && debate.name === politician && cardRef.current) {
      const top = cardRef.current.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: top - 400,
        behavior: 'smooth',
      });
      hasScrolled = true;
    }
  }, [debate.name, politician, location.pathname]);

  return (
    <div
      ref={cardRef}
      key={index}
      className={`flex flex-col md:flex-row gap-4 md:gap-6 p-4 md:p-6 rounded-[24px] min-h-[200px] w-full justify-start md:justify-start items-start shadow-md`}
      style={{
        backgroundColor: debate.name === politician ? '#fff2b5' : 'transparent',
      }}
    >
      <div className="flex flex-col items-start md:items-end min-w-0 md:min-w-[200px] w-full md:w-auto">
        <h3 className="font-['SFProTextMedium'] text-[#222222] text-sm md:text-sm text-right max-w-[200px]">
          {debate.topic}
        </h3>
        <div className="text-sm text-[#515151]"></div>
        <p className="text-sm text-[#515151]">{debate.sub_topics}</p>
        <p className="text-sm text-[#515151] text-right w-full">
          {debate.datetime}
        </p>
        <p
          className="text-sm"
          style={{
            color:
              debate.party == 'Bloc'
                ? '#8AC0DD'
                : debate.party == 'Liberal'
                ? '#FF9999'
                : debate.party == 'Green'
                ? '#A9FA98'
                : debate.party == 'Conservative'
                ? '#AECBF4'
                : debate.party == 'NDP'
                ? '#F7B86D'
                : '#DD3434',
          }}
        >
          {debate.party}
        </p>
      </div>
      <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
        <img
          src={debate.image || 'https://fakeimg.pl/600x400/ffffff/fffcfc'}
          className="w-[80px] h-[80px] md:w-[120px] md:h-[120px] object-contain"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            if (img.src !== 'https://fakeimg.pl/600x400/ffffff/fffcfc') {
              img.src = 'https://fakeimg.pl/600x400/ffffff/fffcfc';
            }
          }}
        />
        <div className="flex flex-col flex-grow">
          <div className="mb-2 flex items-center gap-2">
            <h4 className="text-base md:text-lg font-['SFProTextMedium']">
              <Link to={debate.profile_url}>{debate.name}</Link>
            </h4>
            <p className="text-sm text-[#515151]">{debate.riding}</p>
          </div>
          <p
            className={`text-[#515151] text-sm md:text-base ${
              !isExpanded ? 'line-clamp-4' : ''
            } max-w-full md:max-w-[852px] transition-all duration-300 ease-in-out`}
          >
            {parse(debate.statement, options)}
          </p>
          {!isExpanded && debate.statement.split(' ').length > 40 && (
            <button
              className="text-[#628ECB] mt-2 text-left hover:text-[#4A6B99] transition-colors cursor-pointer"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Read Less' : 'Read More'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DebateCard;
