<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:xml="http://www.w3.org/XML/1998/namespace">

  <xsl:output method="html" encoding="UTF-8" indent="yes" omit-xml-declaration="yes"/>
  <xsl:strip-space elements="*"/>
  <xsl:param name="assets_image_base">assets/images</xsl:param>
  <xsl:param name="assets_audio_base">assets/audio</xsl:param>
  <xsl:param name="assets_video_base">assets/video</xsl:param>

  <xsl:template match="/">
    <div class="tei-fragment">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:group | tei:text | tei:front | tei:body | tei:back">
    <xsl:apply-templates/>
    <xsl:if test="self::tei:group and .//tei:note">
      <section class="endnotes">
        <h2>Notes</h2>
        <ol>
          <xsl:for-each select=".//tei:note">
            <li id="note-{@n}">
              <xsl:apply-templates select="node()"/>
              <xsl:text> </xsl:text>
              <a href="#noteref-{@n}">↩</a>
            </li>
          </xsl:for-each>
        </ol>
      </section>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:titlePage">
    <section class="title-page"><xsl:apply-templates/></section>
  </xsl:template>

  <xsl:template match="tei:div">
    <section class="tei-div">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="tei:head">
        <xsl:variable name="level" select="count(ancestor::tei:div) + 2"/>
        <xsl:choose>
          <xsl:when test="$level = 2"><h2><xsl:apply-templates select="tei:head[1]/node()"/></h2></xsl:when>
          <xsl:when test="$level = 3"><h3><xsl:apply-templates select="tei:head[1]/node()"/></h3></xsl:when>
          <xsl:otherwise><h4><xsl:apply-templates select="tei:head[1]/node()"/></h4></xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:apply-templates select="node()[not(self::tei:head)]"/>
    </section>
  </xsl:template>

  <xsl:template match="tei:head"/>

  <xsl:template match="tei:p">
    <p>
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="tei:cit">
    <div class="cit-block"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:p/tei:cit" priority="20">
    <span class="cit-inline"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:q">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:p/tei:quote" priority="20">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:p/tei:cit/tei:quote" priority="30">
    <q><xsl:apply-templates/></q>
  </xsl:template>

  <xsl:template match="tei:quote">
    <blockquote><xsl:apply-templates/></blockquote>
  </xsl:template>

  <xsl:template match="tei:table">
    <table>
      <xsl:apply-templates/>
    </table>
  </xsl:template>

  <xsl:template match="tei:table/tei:head" priority="20">
    <caption><xsl:apply-templates/></caption>
  </xsl:template>

  <xsl:template match="tei:row">
    <tr><xsl:apply-templates/></tr>
  </xsl:template>

  <xsl:template match="tei:cell">
    <xsl:choose>
      <xsl:when test="@role='label' or @role='header' or @type='head' or @type='header' or parent::tei:row[@role='label' or @role='header' or @type='head' or @type='header']">
        <th><xsl:apply-templates/></th>
      </xsl:when>
      <xsl:otherwise>
        <td><xsl:apply-templates/></td>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:lg">
    <div class="poem-block"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:l">
    <div class="verse-line"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:epigraph">
    <blockquote class="epigraph"><xsl:apply-templates/></blockquote>
  </xsl:template>

  <xsl:template match="tei:figure">
    <figure>
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:call-template name="render-figure-media"/>
      <figcaption>
        <xsl:if test="tei:head">
          <div class="figure-title"><xsl:apply-templates select="tei:head[1]/node()"/></div>
        </xsl:if>
        <xsl:for-each select="tei:p | tei:figDesc">
          <div><xsl:apply-templates select="."/></div>
        </xsl:for-each>
      </figcaption>
    </figure>
  </xsl:template>

  <xsl:template name="render-figure-media">
    <xsl:choose>
      <xsl:when test="tei:graphic[@url]">
        <xsl:variable name="image-src"><xsl:call-template name="resolved-image-src"><xsl:with-param name="url" select="tei:graphic[1]/@url"/></xsl:call-template></xsl:variable>
        <xsl:variable name="image-alt"><xsl:value-of select="normalize-space(tei:head[1])"/></xsl:variable>
        <button type="button" class="figure-zoom-trigger media-zoom-trigger" aria-label="Agrandir l'image">
          <xsl:attribute name="data-lightbox-src"><xsl:value-of select="$image-src"/></xsl:attribute>
          <xsl:attribute name="data-lightbox-alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
          <xsl:if test="string-length($image-alt) &gt; 0">
            <xsl:attribute name="data-lightbox-caption"><xsl:value-of select="$image-alt"/></xsl:attribute>
          </xsl:if>
          <img>
            <xsl:attribute name="src"><xsl:value-of select="$image-src"/></xsl:attribute>
            <xsl:attribute name="alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
          </img>
        </button>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'image/')]">
        <xsl:variable name="image-src"><xsl:call-template name="resolved-image-src"><xsl:with-param name="url" select="tei:media[1]/@url"/></xsl:call-template></xsl:variable>
        <xsl:variable name="image-alt"><xsl:value-of select="normalize-space(tei:head[1])"/></xsl:variable>
        <button type="button" class="figure-zoom-trigger media-zoom-trigger" aria-label="Agrandir l'image">
          <xsl:attribute name="data-lightbox-src"><xsl:value-of select="$image-src"/></xsl:attribute>
          <xsl:attribute name="data-lightbox-alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
          <xsl:if test="string-length($image-alt) &gt; 0">
            <xsl:attribute name="data-lightbox-caption"><xsl:value-of select="$image-alt"/></xsl:attribute>
          </xsl:if>
          <img>
            <xsl:attribute name="src"><xsl:value-of select="$image-src"/></xsl:attribute>
            <xsl:attribute name="alt"><xsl:value-of select="$image-alt"/></xsl:attribute>
          </img>
        </button>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'audio/')]">
        <audio controls="controls"><source><xsl:attribute name="src"><xsl:call-template name="resolved-audio-src"><xsl:with-param name="url" select="tei:media[1]/@url"/></xsl:call-template></xsl:attribute><xsl:attribute name="type"><xsl:value-of select="tei:media[1]/@mimeType"/></xsl:attribute></source></audio>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'video/')]">
        <video controls="controls"><source><xsl:attribute name="src"><xsl:call-template name="resolved-video-src"><xsl:with-param name="url" select="tei:media[1]/@url"/></xsl:call-template></xsl:attribute><xsl:attribute name="type"><xsl:value-of select="tei:media[1]/@mimeType"/></xsl:attribute></source></video>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-image-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_image_base, '/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-audio-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_audio_base, '/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-video-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_video_base, '/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:note">
    <sup class="note-ref" id="noteref-{@n}"><a href="#note-{@n}"><xsl:value-of select="@n"/></a></sup>
  </xsl:template>

  <xsl:template match="tei:ref">
    <a href="{@target}"><xsl:apply-templates/></a>
  </xsl:template>

  <xsl:template match="tei:choice[tei:abbr and tei:expan]" priority="20">
    <abbr>
      <xsl:attribute name="title"><xsl:value-of select="normalize-space(tei:expan[1])"/></xsl:attribute>
      <xsl:apply-templates select="tei:abbr[1]/node()"/>
    </abbr>
  </xsl:template>

  <xsl:template match="tei:choice">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="tei:abbr">
    <abbr><xsl:apply-templates/></abbr>
  </xsl:template>

  <xsl:template match="tei:expan">
    <span class="tei-expan"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:listBibl">
    <section class="tei-div bibliography-block">
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <h2>Bibliographie</h2><ol class="bibl-list"><xsl:apply-templates/></ol>
    </section>
  </xsl:template>

  <xsl:template match="tei:listBibl/tei:bibl" priority="20">
    <li>
      <xsl:if test="@xml:id">
        <xsl:attribute name="id"><xsl:value-of select="@xml:id"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </li>
  </xsl:template>

  <xsl:template match="tei:bibl">
    <cite class="bibl-ref"><xsl:apply-templates/></cite>
  </xsl:template>

  <xsl:template match="tei:list">
    <ul><xsl:apply-templates/></ul>
  </xsl:template>

  <xsl:template match="tei:item">
    <li><xsl:apply-templates/></li>
  </xsl:template>

    <!-- Typographie locale TEI / Métopes.
       normalize-space() permet de tolérer les espaces parasites,
       par exemple rend=" small-caps italic". -->

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' bold ') and contains(concat(' ', normalize-space(@rend), ' '), ' italic ')]" priority="30">
    <strong><em><xsl:apply-templates/></em></strong>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' small-caps ') and contains(concat(' ', normalize-space(@rend), ' '), ' italic ')] | tei:hi[normalize-space(@rend)='small-caps-ital']" priority="30">
    <span class="smallcaps"><em><xsl:apply-templates/></em></span>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' sup ') and contains(concat(' ', normalize-space(@rend), ' '), ' italic ')]" priority="30">
    <sup class="tei-sup"><em><xsl:apply-templates/></em></sup>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' italic ')] | tei:emph" priority="20">
    <em><xsl:apply-templates/></em>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' bold ')]" priority="20">
    <strong><xsl:apply-templates/></strong>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' small-caps ')] | tei:hi[normalize-space(@rend)='smallcaps']" priority="20">
    <span class="smallcaps"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' sup ')]" priority="20">
    <sup class="tei-sup"><xsl:apply-templates/></sup>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' sub ')]" priority="20">
    <sub class="tei-sub"><xsl:apply-templates/></sub>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' underline ')]" priority="20">
    <span class="tei-underline"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:hi[contains(concat(' ', normalize-space(@rend), ' '), ' strikethrough ')]" priority="20">
    <span class="tei-strikethrough"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="tei:pb | tei:lb"><br/></xsl:template>
  <xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>
