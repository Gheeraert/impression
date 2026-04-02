<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:tei="http://www.tei-c.org/ns/1.0"
  xmlns:xml="http://www.w3.org/XML/1998/namespace">

  <xsl:output method="html" encoding="UTF-8" indent="yes" omit-xml-declaration="yes"/>
  <xsl:strip-space elements="*"/>
  <xsl:param name="assets_base">assets</xsl:param>

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
    <section class="tei-div" id="{@xml:id}">
      <xsl:if test="tei:head">
        <xsl:variable name="level" select="count(ancestor::tei:div) + 2"/>
        <xsl:choose>
          <xsl:when test="$level = 2"><h2><xsl:value-of select="normalize-space(tei:head[1])"/></h2></xsl:when>
          <xsl:when test="$level = 3"><h3><xsl:value-of select="normalize-space(tei:head[1])"/></h3></xsl:when>
          <xsl:otherwise><h4><xsl:value-of select="normalize-space(tei:head[1])"/></h4></xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:apply-templates select="node()[not(self::tei:head)]"/>
    </section>
  </xsl:template>

  <xsl:template match="tei:head"/>

  <xsl:template match="tei:p">
    <p id="{@xml:id}"><xsl:apply-templates/></p>
  </xsl:template>

  <xsl:template match="tei:cit">
    <div class="cit-block"><xsl:apply-templates/></div>
  </xsl:template>

  <xsl:template match="tei:quote">
    <blockquote><xsl:apply-templates/></blockquote>
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
    <figure id="{@xml:id}">
      <xsl:call-template name="render-figure-media"/>
      <figcaption>
        <xsl:if test="tei:head">
          <div class="figure-title"><xsl:value-of select="normalize-space(tei:head[1])"/></div>
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
        <img>
          <xsl:attribute name="src"><xsl:call-template name="resolved-image-src"><xsl:with-param name="url" select="tei:graphic[1]/@url"/></xsl:call-template></xsl:attribute>
          <xsl:attribute name="alt"><xsl:value-of select="normalize-space(tei:head[1])"/></xsl:attribute>
        </img>
      </xsl:when>
      <xsl:when test="tei:media[@url and starts-with(@mimeType, 'image/')]">
        <img>
          <xsl:attribute name="src"><xsl:call-template name="resolved-image-src"><xsl:with-param name="url" select="tei:media[1]/@url"/></xsl:call-template></xsl:attribute>
          <xsl:attribute name="alt"><xsl:value-of select="normalize-space(tei:head[1])"/></xsl:attribute>
        </img>
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
      <xsl:otherwise><xsl:value-of select="concat($assets_base, '/images/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-audio-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_base, '/audio/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="resolved-video-src">
    <xsl:param name="url"/>
    <xsl:choose>
      <xsl:when test="contains($url, '://') or starts-with($url, '/') or starts-with($url, 'assets/')"><xsl:value-of select="$url"/></xsl:when>
      <xsl:otherwise><xsl:value-of select="concat($assets_base, '/video/', $url)"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:note">
    <sup class="note-ref" id="noteref-{@n}"><a href="#note-{@n}"><xsl:value-of select="@n"/></a></sup>
  </xsl:template>

  <xsl:template match="tei:ref">
    <a href="{@target}"><xsl:apply-templates/></a>
  </xsl:template>

  <xsl:template match="tei:listBibl">
    <section class="tei-div bibliography-block" id="{@xml:id}"><h2>Bibliographie</h2><ol class="bibl-list"><xsl:apply-templates/></ol></section>
  </xsl:template>

  <xsl:template match="tei:bibl">
    <li id="{@xml:id}"><xsl:apply-templates/></li>
  </xsl:template>

  <xsl:template match="tei:list">
    <ul><xsl:apply-templates/></ul>
  </xsl:template>

  <xsl:template match="tei:item">
    <li><xsl:apply-templates/></li>
  </xsl:template>

  <xsl:template match="tei:hi[@rend='italic'] | tei:emph"><em><xsl:apply-templates/></em></xsl:template>
  <xsl:template match="tei:hi[@rend='bold']"><strong><xsl:apply-templates/></strong></xsl:template>
  <xsl:template match="tei:hi[@rend='smallcaps']"><span class="smallcaps"><xsl:apply-templates/></span></xsl:template>
  <xsl:template match="tei:pb | tei:lb"><br/></xsl:template>
  <xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>
